# Copyright (c) 2025, algo-rhythm.tech and contributors
# For license information, please see license.txt
import os
import frappe

# import frappe
from frappe.model.document import Document


class BloodCellAnalysisConfiguration(Document):
	def validate(self):
		"""Ensure DL model exists at specified path before saving configuration."""
		classification_model_path = self.classification_model_path
		detection_model_path = self.fasterrcnn_model_path

		if not classification_model_path or not os.path.exists(classification_model_path):
			frappe.throw(f"Classification model not found at {classification_model_path}. Please upload a valid model file.")

		if not detection_model_path or not os.path.exists(detection_model_path):
			frappe.throw(f"Detection model not found at {classification_model_path}. Please upload a valid model file.")

	def on_update(self):
		frappe.clear_cache(doctype="Blood Cell Analysis Configuration")  # Clear doctype cache
		frappe.db.commit()  # Commit to apply changes
		frappe.logger().info("Cache Cleared: Blood Cell Analysis Configuration")