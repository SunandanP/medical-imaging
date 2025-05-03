// Copyright (c) 2025, algo-rhythm.tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Cell Detection Image", {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1) {
            setupButtons(frm);
        }
    }
});

// Function to setup buttons based on extraction state
function setupButtons(frm) {
    let extract = false, classify = false;
    // Check if there are extracted cells and show the Classify button if applicable
    frappe.db.get_list("Extracted Cell", {
        filters: { "cell_detection_image": frm.doc.name },
        fields: ["validated_classification"]  // Fetch only necessary fields
        }).then(records => {
            console.log(records);
            let count = records.length;
            if (count > 0) {
                // If extracted cells exist, show the Classify button
                classify = addClassifyButton(frm, records);
            } else {
                extract = addExtractButton(frm, count);
            }
        })
        .catch(err => {
            console.error("Error checking extracted cells:", err);
            frappe.msgprint(__('Error checking extracted cells. Please try refreshing the page.'));
        });

       if (!(extract && classify)) {
            addGenerateReportButton(frm);
        }
}

function addGenerateReportButton(frm){
    frm.add_custom_button(__('Generate RBC Morphology Analysis'), function () {
                    frappe.call({
                        method: "medical_imaging.api.report.create_rbc_morphology_analysis_for_image",
                        args: {cell_detection_image_id: frm.doc.name},
                        callback: function (response) {
                            if (response.message.status === "success") {
                                frappe.msgprint(__('Analysis Complete! Refreshing...'));
                                frm.reload_doc(); // Refresh to switch to Classify button
                            } else {
                                frappe.msgprint(__('Failed to Analyse cells. Please try again.'));
                            }
                        }
                    });
                });
}

// Function to add Extract Cells button (without grouping under Actions)
function addExtractButton(frm, count) {
            if (count === 0) {
                frm.add_custom_button(__('Extract Cells'), function () {
                    frappe.call({
                        method: "medical_imaging.api.cell_extraction.extract_cells",
                        args: {cell_detection_image_id: frm.doc.name},
                        callback: function (response) {
                            if (response.message.status === "success") {
                                frappe.msgprint(__('Cells extracted successfully! Refreshing...'));
                                frm.reload_doc(); // Refresh to switch to Classify button
                            } else {
                                frappe.msgprint(__('Failed to extract cells. Please try again.'));
                            }
                        }
                    });
                });
                return true;
            }

            return false;
}

// Function to add Classify Extracted Cells button (without grouping under Actions)
function addClassifyButton(frm, records) {
    if (!(records[0]["validated_classification"] === "Select" || records[1]["validated_classification"] === "Select")) {
        console.log(records[0].validated_classification, "Hehe")
        return false;
    }

    frm.add_custom_button(__('Classify Extracted Cells'), function() {
        frappe.call({
            method: "medical_imaging.api.classification.enqueue_classification",
            args: { cell_detection_image_id: frm.doc.name },
            callback: function(response) {
                if (response.message.status === "queued") {
                    frappe.msgprint(__('Classification started in the background. Refresh to see updates.'));
                    // Start polling for job completion
                    frappe.realtime.on("classification_complete", function(data) {
                    frappe.msgprint(__('Classification completed. Navigating to Extracted Cells...'));
                    navigateToExtractedCells(data.cell_detection_image_id);
                    });
                } else {
                    frappe.msgprint(__('Failed to queue classification. Please check logs.'));
                }
            }
        });
    });
    return true;
}

function navigateToExtractedCells(cell_detection_image_id) {
    // Navigate to the "Extracted Cell" doctype with a filter
    frappe.set_route('List', 'Extracted Cell', {
        cell_detection_image: cell_detection_image_id // Filter by the current Cell Detection Image
    });
}