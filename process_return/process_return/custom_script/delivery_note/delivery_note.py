from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json

def custom_validate(doc,method):
	close_closeable_dn(doc)

def custom_update(doc,method):
	close_closeable_dn(doc)

def close_closeable_dn(doc):

	if doc.status == "To Bill":
		print("update after submit=======")
