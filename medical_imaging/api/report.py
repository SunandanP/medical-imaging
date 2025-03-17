import frappe

@frappe.whitelist()
def create_rbc_morphology_analysis_for_image():
    """
    API to query Extracted Cells for a specific cell_detection_image,
    count cell types, and create an RBC Morphology Analysis record.
    """
    try:


        # Validate input
        if frappe.request.method != "POST":
            return {"message": "Invalid request method. Use POST.", "status": "failed"}

        cell_detection_image = frappe.form_dict.get("cell_detection_image_id")

        # Fetch all Extracted Cells for the given cell_detection_image
        extracted_cells = frappe.get_all(
            "Extracted Cell",
            filters={"cell_detection_image": cell_detection_image},
            fields=["name", "primary_classification"]
        )

        if not extracted_cells:
            return {"status": "error", "message": "No extracted cells found for the given cell_detection_image"}

        # Initialize counters
        total_cells = len(extracted_cells)
        normal_cell_count = 0
        sickle_cell_count = 0
        other_cell_count = 0

        # Count cells based on classification
        for cell in extracted_cells:
            if cell.primary_classification == "Circular":
                normal_cell_count += 1
            elif cell.primary_classification == "Elongated":
                sickle_cell_count += 1
            elif cell.primary_classification == "Other":
                other_cell_count += 1

        # Calculate percentages
        normal_cells_percentage = (normal_cell_count / total_cells) * 100 if total_cells > 0 else 0
        sickle_cells_percentage = (sickle_cell_count / total_cells) * 100 if total_cells > 0 else 0
        other_cells_percentage = (other_cell_count / total_cells) * 100 if total_cells > 0 else 0

        blood_smear_image = frappe.db.get_value("Cell Detection Image", cell_detection_image, "blood_smear_image")
        patient = frappe.db.get_value("Blood Smear Image", blood_smear_image, "patient")

        # Create RBC Morphology Analysis record
        rbc_doc = frappe.get_doc({
            "doctype": "RBC Morphology Analysis",
            "patient": patient,
            "cell_detection_image": cell_detection_image,
            "cells_examined": total_cells,
            "normal_cell_count": normal_cell_count,
            "sickle_cell_count": sickle_cell_count,
            "other_cell_count": other_cell_count,
            "normal_cells_percentage": round(normal_cells_percentage, 2),
            "sickle_cells_percentage": round(sickle_cells_percentage, 2),
            "other_cells_percentage": round(other_cells_percentage, 2)
        })
        rbc_doc.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "RBC Morphology Analysis record created successfully.",
            "rbc_morphology_analysis": rbc_doc.name
        }

    except Exception as e:
        frappe.log_error(f"Error in create_rbc_morphology_analysis_for_image: {str(e)}", "RBC Morphology Analysis")
        return {"status": "error", "message": str(e)}