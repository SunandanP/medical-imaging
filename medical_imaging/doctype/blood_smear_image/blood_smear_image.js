// Copyright (c) 2025, algo-rhythm.tech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Blood Smear Image', {
    refresh: function(frm) {
        // Ensure the button is only shown when the document is in submitted state (docstatus = 1)
        if (frm.doc.docstatus === 1) {
            frappe.db.get_value('Cell Detection Image', { blood_smear_image: frm.doc.name }, 'name')
                .then(response => {
                    if (!response.message || !response.message.name) {
                        let button = frm.add_custom_button(__('Detect Cells'), function() {
                            // Show infinite progress bar
                            let progress_bar = frappe.show_progress(__('Detecting Cells...'), 80, 100);

                            frappe.call({
                                method: 'medical_imaging.api.cell_detection.detect_cells',
                                args: {
                                    blood_smear_id: frm.doc.name
                                },
                                callback: function(response) {
                                    // Hide progress bar
                                    frappe.hide_progress();

                                    if (response.message) {
                                        let cell_detection_id = response.message.cell_detection_image;

                                        // Show acknowledgment message before redirecting
                                        frappe.msgprint(__('Cells Detected Successfully! Redirecting you to the results...'));

                                        // Wait for 1.5 seconds before redirecting
                                        setTimeout(() => {
                                            frappe.set_route("Form", "Cell Detection Image", cell_detection_id);
                                        }, 2000);
                                    } else {
                                        frappe.msgprint(__('Cell Detection Failed!'));
                                    }
                                }
                            });
                        });
                    }
                });
        }
    }
});
