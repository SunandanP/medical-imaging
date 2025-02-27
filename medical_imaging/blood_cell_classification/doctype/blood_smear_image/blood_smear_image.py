# Copyright (c) 2025, algo-rhythm.tech and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class BloodSmearImage(Document):
	def before_save(self):
		from frappe.utils import now, getdate
		self.capture_date = getdate(now())
