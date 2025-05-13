import frappe
from frappe.utils import formatdate

@frappe.whitelist()
def send_rbc_report_email(docname):
    try:
        doc = frappe.get_doc("RBC Morphology Analysis", docname)
        patient = frappe.get_doc("Patient", doc.patient)

        # Generate PDF for the specific document with the correct settings
        pdf_data = frappe.get_print(
            doctype="RBC Morphology Analysis",
            name=doc.name,
            print_format="Patient Report Mail",
            as_pdf=True,
            letterhead="HemoScan",
        )

        # Render custom email body
        email_html = frappe.render_template("templates/emails/rbc_report_email.html", {
            "doc": doc,
            "patient_name": patient.full_name,
            "test_date": formatdate(doc.creation),
            "report_id": doc.name,
            "generation_date": formatdate(doc.modified),
        })

        if not patient.email:
            frappe.throw("No email address found for patient.")

        # Send the email with PDF attachment
        frappe.sendmail(
            recipients=[patient.email],
            subject=f"{patient.full_name}, Your RBC Morphology Report from HemoScan is Ready",
            message=email_html,
            attachments=[{
                "fname": f"{doc.name}.pdf",
                "fcontent": pdf_data
            }],
            delayed=False
        )

        return {"status": "success", "message": f"Email sent to {patient.email}"}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "RBC Report Email Error")
        return {"status": "error", "message": str(e)}
