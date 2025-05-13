frappe.ui.form.on("RBC Morphology Analysis", {
    refresh(frm) {
        if (!frm.doc.approved_by) {
            frm.add_custom_button(__('Approve'), async function() {
                const current_user = frappe.session.user;
                const current_date = frappe.datetime.get_today();

                // Update approval fields
                await frm.set_value('approved_by_link', current_user);
                await frm.set_value('approval_date', current_date);

                await frm.save(); // Save the document first

                // Apply workflow only if state is Pending Approval
                if (frm.doc.workflow_state === "Pending Approval") {
                    frappe.call({
                        method: "frappe.model.workflow.apply_workflow",
                        args: {
                            doc: frm.doc,  // pass the full document
                            action: "Approve"
                        },
                        callback: function(r) {
                            if (!r.exc) {
                                frappe.show_alert({
                                    message: __('Document approved successfully!'),
                                    indicator: 'green'
                                }, 3);
                                frappe.call({
                                    method: "medical_imaging.api.send_mail.send_rbc_report_email",
                                    args: {
                                        docname: frm.doc.name,
                                    },
                                    callback: function(r) {
                                        if (r.message && r.message.status === "success") {
                                            frappe.msgprint(r.message.message);
                                        } else {
                                            frappe.msgprint({
                                                title: "Error",
                                                message: r.message.message || "Failed to send email.",
                                                indicator: "red"
                                            });
                                        }
                                    }
                                });
                                frm.reload(); // Refresh to reflect the workflow change
                            }
                        }
                    });
                } else {
                    frm.reload(); // fallback reload if not in workflow state
                }
            }).addClass('btn-primary');
        }
    },
});
