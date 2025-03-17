// Copyright (c) 2025, algo-rhythm.tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("RBC Morphology Analysis", {
    refresh(frm) {
        // Only show the Approve button if the document is not already approved
        // and if the user has permission to approve
        if (!frm.doc.approved_by) {
            frm.add_custom_button(__('Approve'), function() {
                // Get current user
                const current_user = frappe.session.user;
                // Get current date in yyyy-mm-dd format
                const current_date = frappe.datetime.get_today();

                // Update the fields
                frm.set_value('approved_by', current_user);
                frm.set_value('approval_date', current_date);

                // Save the document
                frm.save();
                frm.reload()

                frappe.show_alert({
                    message: __('Document approved successfully!'),
                    indicator: 'green'
                }, 3);
            }).addClass('btn-primary');
        }
    },
});