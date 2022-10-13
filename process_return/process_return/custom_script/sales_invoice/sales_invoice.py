# -*- coding: utf-8 -*-
# Copyright (c) 2020, AK and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from process_return.process_return.doctype.process_return_ui.process_return_ui import proceed_to_return_dn

def custom_validate(doc,method):
	validate_commission(doc,method)
	pass


def validate_commission(doc,method):
	if doc.sales_partner:
		act_commission_rate = frappe.db.get_value("Sales Partner",doc.sales_partner,"commission_rate")
		act_commission = doc.base_grand_total * act_commission_rate/100
		if doc.total_commission > act_commission:
			frappe.throw("Total Commsion Cannot be More than commision rate")


def custom_submit(doc,method):
	if doc.is_return:
		invoices = [doc.name]
		proceed_to_return_dn(invoices)