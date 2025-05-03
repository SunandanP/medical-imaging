// Copyright (c) 2025, algo-rhythm.tech and contributors
// For license information, please see license.txt
frappe.ui.form.on('Extracted Cell', {
    onload: function(frm) {
        if (frm.doc.original_image && frm.doc.xai_visualisation) {
            // Get the image URLs
            let originalImage = frm.doc.original_image;
            let xaiImage = frm.doc.xai_visualisation;

            // Resize images using HTML attributes (no backend resizing needed)
            let html = `
                <div style="display: flex; gap: 20px; justify-content: center;">
                    <div>
                        <img src="${originalImage}" width="300" height="auto" style="border: 1px solid #ccc; border-radius: 5px;">
                        <p style="text-align: center; font-weight: bold;">Original Image</p>
                    </div>
                    <div>
                        <img src="${xaiImage}" width="300" height="auto" style="border: 1px solid #ccc; border-radius: 5px;">
                        <p style="text-align: center; font-weight: bold;">XAI Visualisation</p>
                    </div>
                </div>
            `;

            // Render images in the custom HTML field
            frm.fields_dict.image_display.$wrapper.html(html);
        }
    }
});

