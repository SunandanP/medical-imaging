import torch
from .EfficientNetB4 import EfficientNetB4
from torchvision import transforms
from PIL import Image
import frappe
from frappe.utils.file_manager import get_file_path

# Load model architecture (EfficientNetB4 in this case)
def load_model():
    model = EfficientNetB4(3)
    MODEL_PATH = frappe.get_site_path(
            "/Users/user/Codes/Personal/BE/medical-imaging-system/apps/medical_imaging/medical_imaging/prediction_models/EfficientNetB4.pth")
    model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu')))
    model.eval()
    return model


# Load model (ensure the model architecture is properly defined)
MODEL = load_model()

# Image preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])


@frappe.whitelist(allow_guest=True)
def classify_image():
    """
    Classifies an image using the deep learning model.
    The image is expected to be uploaded as a file in a multipart form request.
    :return: JSON result with classification
    """
    classes = ["Circular", "Elongated", "Other"]
    try:
        # Get the uploaded image file from the request
        extracted_cell_id = frappe.form_dict.get("extracted_cell_id")
        extracted_cell_image = frappe.get_doc("Extracted Cell", extracted_cell_id)

        full_path = get_file_path(extracted_cell_image.cell_image)

        # Read the image as a PIL Image
        image = Image.open(full_path)

        # Apply transformations and add batch dimension
        image = transform(image).unsqueeze(0)

        # Run inference
        with torch.no_grad():
            output = MODEL(image)
            predicted_class = torch.argmax(output, dim=1).item()

        # Return the prediction result
        return {"status": "success", "prediction": classes[predicted_class]}

    except Exception as e:
        # Log error and return a failure response
        frappe.log_error(f"Model Inference Error: {str(e)}", "Deep Learning API")
        return {"status": "error", "message": str(e)}