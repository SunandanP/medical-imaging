import frappe
import json
import os
import base64
from PIL import Image, ImageDraw
from frappe.utils.file_manager import get_file_path


@frappe.whitelist(allow_guest=True)
def extract_cells():
    """
    API to extract individual cell images from the original Blood Smear Image.
    :return: JSON response with extracted cell details.
    """
    try:
        if frappe.request.method != "POST":
            return {"message": "Invalid request method. Use POST.", "status": "failed"}

        cell_detection_image_id = frappe.form_dict.get("cell_detection_image_id")
        cell_detection_image_doc = frappe.get_doc("Cell Detection Image", cell_detection_image_id)

        # Fetch Blood Smear Image from linked Doctype
        blood_smear_doc = frappe.get_doc("Blood Smear Image", cell_detection_image_doc.blood_smear_image)
        blood_smear_image_path = get_file_path(blood_smear_doc.image)

        extracted_cells = []
        for result in cell_detection_image_doc.detection_result:
            img = Image.open(blood_smear_image_path).convert("RGB")
            bbox = json.loads(result.bounding_coordinates)
            classification = result.classification

            x1, y1, x2, y2 = map(int, bbox)

            # Calculate the midpoint of the bounding box
            mid_x = (x1 + x2) // 2
            mid_y = (y1 + y2) // 2

            # Define the 80x80 bounding square around the midpoint
            half_size = 40  # Half of 80 pixels
            new_x1 = max(0, mid_x - half_size)
            new_y1 = max(0, mid_y - half_size)
            new_x2 = new_x1 + 80
            new_y2 = new_y1 + 80

            cropped_img = img.crop((new_x1, new_y1, new_x2, new_y2))
            extracted_path = f'bloodcell.classify/private/files/{cell_detection_image_id}_{new_x1}_{new_y1}.png'
            cropped_img.save(extracted_path)

            # Create a drawing context
            draw = ImageDraw.Draw(img)

            color = "red"  # You can customize the color based on the label
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)

            cropped_img_cd = img.crop((new_x1, new_y1, new_x2, new_y2))
            extracted_path_cd = f'bloodcell.classify/private/files/{cell_detection_image_id}_{new_x1}_{new_y1}_CD.png'
            cropped_img_cd.save(extracted_path_cd)

            with open(extracted_path, "rb") as img_file:
                encoded_image = base64.b64encode(img_file.read()).decode("utf-8")

            with open(extracted_path_cd, "rb") as image_file_cd:
                encoded_image_cd = base64.b64encode(image_file_cd.read()).decode("utf-8")

            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": f"{cell_detection_image_id}_{new_x1}_{new_y1}.png",
                "file_url": f"/private/files/{cell_detection_image_id}_{new_x1}_{new_y1}.png",
                "content": encoded_image,
                "decode": True,
                "is_private": True
            })
            file_doc.insert(ignore_permissions=True)

            file_doc_cd = frappe.get_doc({
                "doctype": "File",
                "file_name": f"{cell_detection_image_id}_{new_x1}_{new_y1}_CD.png",
                "file_url": f"/private/files/{cell_detection_image_id}_{new_x1}_{new_y1}_CD.png",
                "content": encoded_image_cd,
                "decode": True,
                "is_private": True
            })
            file_doc_cd.insert(ignore_permissions=True)

            extracted_cell_doc = frappe.get_doc({
                "doctype": "Extracted Cell",
                "cell_detection_image": cell_detection_image_id,
                "cell_image": file_doc.file_url,
                "primary_classification": classification,
                "cell_detection_result": file_doc_cd.file_url,
                "cell_number": len(extracted_cells) + 1
            })
            extracted_cell_doc.insert(ignore_permissions=True)

            extracted_cells.append({
                "cell_image_url": file_doc.file_url,
                "predicted_label": classification
            })

            if os.path.exists(extracted_path):
                os.remove(extracted_path)

            if os.path.exists(extracted_path_cd):
                os.remove(extracted_path_cd)

        return {
            "message": "Cells extracted and saved successfully!",
            "status": "success",
            "extracted_cells": extracted_cells
        }

    except Exception as e:
        error_message = str(e)[:130]
        frappe.log_error(f"Error in cell extraction: {error_message}")
        return {"message": f"Error: {str(e)}", "status": "failed"}
