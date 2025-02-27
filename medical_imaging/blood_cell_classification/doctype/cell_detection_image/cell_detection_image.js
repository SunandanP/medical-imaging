// Copyright (c) 2025, algo-rhythm.tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cell Detection Image", {
    refresh: function(frm) {
        // Ensure the button is shown only when the document is submitted (docstatus = 1)
        if (frm.doc.docstatus === 1) {
            frappe.db.count("Extracted Cell", { detection_image: frm.doc.name })
                .then(count => {
                    if (count > 0) {
                        frm.add_custom_button(__('Classify Extracted Cells'), function() {
                            // Show an initial progress bar
                            let progress_bar = frappe.show_progress(__('Classifying Cells...'), 0, count);

                            frappe.call({
                                method: "frappe.client.get_list",
                                args: {
                                    doctype: "Extracted Cell",
                                    filters: { detection_image: frm.doc.name },
                                    fields: ["name"]
                                },
                                callback: function(response) {
                                    let extracted_cells = response.message;
                                    if (!extracted_cells.length) {
                                        frappe.msgprint(__('No extracted cells found for classification.'));
                                        return;
                                    }

                                    let total = extracted_cells.length;
                                    let completed = 0;

                                    extracted_cells.forEach(cell => {
                                        frappe.call({
                                            method: "medical_imaging.api.classification.classify_image",
                                            args: { extracted_cell_id: cell.name },
                                            callback: function() {
                                                completed++;
                                                frappe.show_progress(__('Classifying Cells...'), completed, total);

                                                // If classification is complete
                                                if (completed === total) {
                                                    frappe.hide_progress();
                                                    frappe.msgprint(__('All cells classified successfully! Redirecting...'));

                                                    setTimeout(() => {
                                                        frappe.set_route("List", "Extracted Cells", { "detection_image": frm.doc.name });
                                                    }, 2000);
                                                }
                                            }
                                        });
                                    });
                                }
                            });
                        });
                    }
                });
        }
    }
});
