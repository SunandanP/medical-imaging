import os
import torch
from torchvision import transforms
from PIL import Image
import frappe
from frappe.utils.file_manager import get_file_path
import torch.nn as nn
import timm
import numpy as np
import cv2
import base64
from io import BytesIO


class EfficientNetB4(nn.Module):
    def __init__(self, num_classes):
        super(EfficientNetB4, self).__init__()
        self.efficientnet_b4 = timm.create_model('tf_efficientnet_b4', pretrained=True)
        num_ftrs = self.efficientnet_b4.get_classifier().in_features
        self.efficientnet_b4.classifier = nn.Linear(num_ftrs, num_classes)

    def forward(self, x):
        x = self.efficientnet_b4(x)
        return x

def load_model(model_path, num_classes):
    model = EfficientNetB4(num_classes)
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()
    return model

configurations = frappe.get_single("Blood Cell Analysis Configuration")
model_path = configurations.classification_model_path
num_classes = 3  # Change this based on your dataset
model = load_model(model_path, num_classes)
device = torch.device('cpu')

class GradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.feature_maps = None
        self.target_layer.register_forward_hook(self.save_feature_maps)
        self.target_layer.register_backward_hook(self.save_gradients)

    def save_feature_maps(self, module, input, output):
        self.feature_maps = output.detach()

    def save_gradients(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate_cam(self):
        grad_weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        cam = torch.mul(self.feature_maps, grad_weights)
        cam = torch.sum(cam, dim=1)
        cam = torch.relu(cam)
        cam -= cam.min()
        cam /= cam.max()
        return cam.detach().cpu().numpy()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

def load_image(image_path):
    img = Image.open(image_path).convert('RGB')
    img_tensor = transform(img).unsqueeze(0)
    return img, img_tensor

def classify_extracted_cell(cell_id):
    classes = ["Circular", "Elongated", "Other"]
    try:
        if not cell_id:
            return {"status": "error", "message": "extracted_cell_id is required"}

        extracted_cell = frappe.get_doc("Extracted Cell", cell_id)
        if not extracted_cell.cell_image:
            return {"status": "error", "message": "cell_image not found"}

        image_path = get_file_path(extracted_cell.cell_image)
        if not image_path:
            return {"status": "error", "message": "Image file not found on the server"}

        original_img = Image.open(image_path).convert('RGB')
        img_tensor = transform(original_img).unsqueeze(0)

        target_layer = model.efficientnet_b4.conv_head
        gradcam = GradCAM(model, target_layer)

        output = model(img_tensor)
        pred_class = output.argmax(dim=1).item()

        model.zero_grad()
        output[0, pred_class].backward()

        heatmap = gradcam.generate_cam()[0]

        # Resize and smooth the heatmap
        heatmap = cv2.resize(heatmap, (original_img.width, original_img.height))
        heatmap = cv2.GaussianBlur(heatmap, (5, 5), 0)  # Add smoothing
        heatmap = np.uint8(255 * heatmap)
        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

        # Convert original image to BGR for OpenCV
        img_cv = np.array(original_img)
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

        # Overlay heatmap with adjusted weights
        superimposed_img = cv2.addWeighted(img_cv, 0.5, heatmap, 0.5, 0)

        # Convert BGR to RGB for saving
        superimposed_img_rgb = cv2.cvtColor(superimposed_img, cv2.COLOR_BGR2RGB)

        # Save in memory instead of disk
        buffered = BytesIO()
        pil_image = Image.fromarray(superimposed_img_rgb)
        pil_image.save(buffered, format="JPEG")
        file_content = buffered.getvalue()
        file_content_base64 = base64.b64encode(file_content).decode('utf-8')

        # Upload to Frappe
        file_name = f"gradcam_{cell_id}.jpg"
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "content": file_content_base64,
            "decode": True,
            "is_private": True
        })
        file_doc.insert(ignore_permissions=True)

        # Update the Extracted Cell document
        extracted_cell.reload()
        extracted_cell.validated_classification = classes[pred_class]
        extracted_cell.xai_image = file_doc.file_url
        extracted_cell.save(ignore_permissions=True)

        return {"status": "success", "validated_classification": classes[pred_class], "xai_image": file_doc.file_url}

    except Exception as e:
        frappe.log_error(f"Classification API Error: {str(e)}", "Deep Learning API")
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def enqueue_classification(cell_detection_image_id):
    try:
        frappe.enqueue("medical_imaging.api.classification.classify_all_extracted_cells",
                       queue='long',
                       job_name=f"Classify Cells {cell_detection_image_id}",
                       timeout=600,
                       callback="medical_imaging.api.classification.on_classification_complete",
                       enqueue_after_commit=True,
                       cell_detection_image_id=cell_detection_image_id)
        return {"status": "queued"}
    except Exception as e:
        frappe.log_error(f"Enqueue Error: {str(e)}", "Deep Learning API")
        return {"status": "error", "message": str(e)}

def classify_all_extracted_cells(cell_detection_image_id, **kwargs):
    extracted_cells = frappe.get_all("Extracted Cell",
                                     filters={"cell_detection_image": cell_detection_image_id},
                                     pluck="name")

    if not extracted_cells:
        frappe.msgprint("No extracted cells found for classification.")
        return

    for cell_id in extracted_cells:
        classify_extracted_cell(cell_id)

    frappe.msgprint(f"Classification completed for {len(extracted_cells)} cells.")
    on_classification_complete(cell_detection_image_id)

@frappe.whitelist()
def on_classification_complete(cell_detection_image_id):
    frappe.publish_realtime("classification_complete", {
        "cell_detection_image_id": cell_detection_image_id
    })