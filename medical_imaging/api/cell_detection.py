import base64
import json
import os

import numpy as np
import torch
import torchvision
import torchvision.transforms as T
from PIL import Image, ImageDraw
from torchvision.models.detection import fasterrcnn_resnet50_fpn
import frappe
from frappe.utils.file_manager import get_file_path
from medical_imaging.doctype.blood_cell_analysis_configuration.blood_cell_analysis_configuration import ( get_detection_threshold_configuration, get_detection_average_area_tolerance)

configurations = frappe.get_single("Blood Cell Analysis Configuration")
# Load Faster R-CNN model
model_path = configurations.fasterrcnn_model_path

def get_predictions(image_path):
    device = torch.device("cpu")

    # Load Faster R-CNN model
    model = fasterrcnn_resnet50_fpn(weights=None, progress=False)

    # Get the number of input features for the classifier
    in_features = model.roi_heads.box_predictor.cls_score.in_features

    # Replace the head with a new one (for num_classes + background)
    model.roi_heads.box_predictor = torchvision.models.detection.faster_rcnn.FastRCNNPredictor(in_features, 4)

    model.load_state_dict(torch.load(model_path, map_location=device))

    # Set the model to evaluation mode
    model.eval()
    model.to(device)

    # Load and preprocess the image
    img = Image.open(image_path).convert("RGB")  # Load image and convert to RGB
    original_width, original_height = img.size
    transforms = T.Compose([T.Resize((2000, 2000)), T.ToTensor()])
    img_tensor = transforms(img).to(device)  # Apply transformations

    # Perform inference (get predicted bounding boxes and scores)
    with torch.no_grad():
        prediction = model([img_tensor])[0]

    pred_boxes = prediction['boxes'].cpu().numpy()
    pred_labels = prediction['labels'].cpu().numpy()
    scores = prediction['scores'].cpu().numpy()

    # Scale bounding boxes back to the original image size
    scale_x = original_width / 2000  # Scaling factor for width
    scale_y = original_height / 2000  # Scaling factor for height

    # Adjust bounding box coordinates to match the original image size
    pred_boxes[:, 0] *= scale_x  # x1
    pred_boxes[:, 1] *= scale_y  # y1
    pred_boxes[:, 2] *= scale_x  # x2
    pred_boxes[:, 3] *= scale_y  # y2

    # Calculate the area of each detected item
    areas = (pred_boxes[:, 2] - pred_boxes[:, 0]) * (pred_boxes[:, 3] - pred_boxes[:, 1])

    # Compute the average area of all detected items
    average_area = np.mean(areas)

    # Define the tolerance (15%)
    tolerance = get_detection_average_area_tolerance()/100
    upper_limit = average_area * (1 + tolerance)

    # Filter out items whose area exceeds the average area by more than 15%
    valid_indices = areas <= upper_limit
    filtered_boxes = pred_boxes[valid_indices]
    filtered_labels = pred_labels[valid_indices]
    filtered_scores = scores[valid_indices]

    return filtered_boxes, filtered_labels, filtered_scores

def save_img_prediction(prediction, img_path, id, score_threshold):
    pred_boxes, pred_labels, scores = prediction

    class_names = ['background', 'circular', 'elongated', 'other']

    # Filter predictions based on the score threshold
    high_conf_boxes = pred_boxes[scores >= score_threshold]
    high_conf_labels = pred_labels[scores >= score_threshold]

    # Load the image using PIL
    img = Image.open(img_path).convert("RGB")

    # Create a drawing context
    draw = ImageDraw.Draw(img)

    # Draw bounding boxes on the image
    for box, label in zip(high_conf_boxes, high_conf_labels):
        x1, y1, x2, y2 = box
        color = "red"  # You can customize the color based on the label
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)


    # Save the image with bounding boxes
    image_path = f'bloodcell.classify/private/files/{id}cell_detection_image.png'

    # Save the image
    img.save(image_path)

    # Encode the image in base64
    with open(image_path, "rb") as img_file:
        encoded_image = base64.b64encode(img_file.read()).decode("utf-8")

    # Create a File document in Frappe
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": f"cell_detection_image.png",
        "file_url": f"/private/files/cell_detection_image.png",  # Ensure correct file path
        "content": encoded_image,
        "decode": True,
        "is_private": True
    })

    file_doc.insert(ignore_permissions=True)
    frappe.db.commit()

    if os.path.exists(image_path):
        os.remove(image_path)

    return high_conf_boxes, high_conf_labels, scores[scores >= score_threshold], file_doc.file_url

@frappe.whitelist(allow_guest=True)
def detect_cells():
    """
    API to detect sickle-shaped red blood cells (RBCs) in a blood smear image.
    :return: JSON response with bounding boxes, labels, and confidence scores.
    """
    try:
        if frappe.request.method != "POST":
            return {"message": "Invalid request method. Use POST.", "status": "failed"}

        classes = ["Circular", "Elongated", "Other"]
        blood_smear_id = frappe.form_dict.get("blood_smear_id")
        blood_smear_image = frappe.get_doc("Blood Smear Image", blood_smear_id)

        full_path = get_file_path(blood_smear_image.image)
        prediction = get_predictions(full_path)
        score_threshold = get_detection_threshold_configuration()/100
        prediction = save_img_prediction(prediction, full_path, blood_smear_id, score_threshold=score_threshold)

        boxes, labels, scores, file_url = prediction
        boxes = boxes.tolist()
        labels = labels.tolist()
        scores = scores.tolist()

        # Store results in the Cell Detection Image doctype
        cell_detection_image = frappe.get_doc({
            "doctype": "Cell Detection Image",
            "blood_smear_image": blood_smear_id,
            "cell_detection_image": file_url,
            "detection_result": []
        })

        for box, label, score in zip(boxes, labels, scores):
            cell_detection_image.append("detection_result", {
                "classification": classes[label-1],
                "confidence_score": json.dumps(score),
                "bounding_coordinates": json.dumps(box)
            })

        cell_detection_image.insert(ignore_permissions=True)
        frappe.db.commit()

        print(cell_detection_image.name)
        return {
            "message": "Detection results saved successfully!",
            "status": "success",
            "cell_detection_image": cell_detection_image.name,
            "detections": {
                "bounding_boxes": boxes,
                "labels": labels,
                "confidence_scores": scores
            }
        }

    except Exception as e:
        error_message = str(e)[:130]
        frappe.log_error(f"Error in cell detection: {error_message}")
        return {"message": f"Error: {str(e)}", "status": "failed"}