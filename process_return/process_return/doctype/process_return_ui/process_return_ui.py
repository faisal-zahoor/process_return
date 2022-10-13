# -*- coding: utf-8 -*-
# Copyright (c) 2020, AK and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from erpnext.controllers.sales_and_purchase_return import make_return_doc
from itertools import groupby
from operator import itemgetter

from frappe.model.mapper import get_mapped_doc
import datetime
from frappe.contacts.doctype.address.address import get_company_address
from frappe.utils import cint, flt
from frappe import _

class ProcessReturnUI(Document):
	pass



def get_delivery_notes_against_sales_invoices(item_list):

	""" returns a return delivery note against return sales invoices"""


	so_dn_map = frappe._dict()
	so_item_rows = list(set([d.so_detail for d in item_list]))

	if so_item_rows:
		delivery_notes = frappe.db.sql("""
			select di.parent, di.so_detail
			from `tabDelivery Note Item` di, `tabDelivery Note` dn
			where di.docstatus=1 and is_return=1 and di.parent = dn.name 
			and so_detail in (%s)
			group by so_detail, parent
		""" % (', '.join(['%s']*len(so_item_rows))), tuple(so_item_rows), as_dict=1)

		for dn in delivery_notes:
			so_dn_map.setdefault(dn.so_detail, []).append(dn.parent)

	return so_dn_map



def check_retrun_againts_sales_invoice(inv_doc):

	return_against_invoice = inv_doc.return_against
	return_inv_doc = frappe.get_doc("Sales Invoice",return_against_invoice)
	return_against_si_dns = get_delivery_notes_against_sales_order(return_inv_doc.items)
	# print(return_against_si_dns,return_inv_doc.name,inv_doc.name,"return against===")
	return return_against_si_dns



@frappe.whitelist()
def get_return_invoice(doc):
	# get return invoices within date range

	doc=json.loads(doc)
	from_date = doc.get("from_date")
	to_date = doc.get("to_date")
	return_invoices = [d.name for d in frappe.get_all("Sales Invoice", 
				filters={"is_return": 1, "docstatus": 1,'update_stock':0,
				"posting_date": ["between", [from_date, to_date]]})]


	_return_invoices = []
	for inv in return_invoices:

		inv_doc = frappe.get_doc("Sales Invoice",inv)

		return_against_si_dns = check_retrun_againts_sales_invoice(inv_doc)

		if return_against_si_dns:

			existing_return_dn  = get_delivery_notes_against_sales_invoices(inv_doc.items)

			# print(existing_return_dn,"==existing_return_dn")
			if not existing_return_dn:
				_return_invoices.append(inv)

	
	return _return_invoices

def update_inv_qty(response,si_qtys):

	for items in response.items:
		qty = si_qtys.get(items.so_detail)
		items.qty = qty



def get_delivery_notes_against_sales_order(item_list):
	so_dn_map = frappe._dict()
	so_item_rows = list(set([d.so_detail for d in item_list]))

	if so_item_rows:
		delivery_notes = frappe.db.sql("""
			select parent, so_detail
			from `tabDelivery Note Item`
			where docstatus=1 and so_detail in (%s)
			group by so_detail, parent
		""" % (', '.join(['%s']*len(so_item_rows))), tuple(so_item_rows), as_dict=1)

		for dn in delivery_notes:
			so_dn_map.setdefault(dn.so_detail, []).append(dn.parent)

	return so_dn_map



@frappe.whitelist()
def proceed_to_return_dn(invoices):
	""" * generic method to return delivery notes 
		* accepts list of invoices = ["EX/20-21-10012",EX/20-21-10011]
		* will create return delivery notes against the invoices items

	"""


	if isinstance(invoices,str):
		invoices = json.loads(invoices)
	
	try:
		if isinstance(invoices, basestring):
			invoices = json.loads(invoices)
	except:
		pass


	sales_orders  =[]
	invoices_items = []
	si_qtys={}
	
	for inv in invoices:
		
		inv_doc = frappe.get_doc('Sales Invoice',inv)
		invoices_items+=inv_doc.items
		for itm in inv_doc.items:
			if itm.so_detail:
				si_qtys[itm.so_detail] = itm.qty

	# print("after first loop",datetime.datetime.now())
	# print("Before geting DN ",datetime.datetime.now())
	delivery_notes = get_delivery_notes_against_sales_order(invoices_items)

	
	
	delivery_notes=list(delivery_notes.values())
	
	all_dns = []
	for dn in delivery_notes:
		all_dns += dn

	all_dns = list(set(all_dns))

	# print("Before Creating Return DN ",datetime.datetime.now())
	for dn in all_dns:
		try:
			response = make_return_doc("Delivery Note", dn, target_doc=None)
			update_inv_qty(response,si_qtys)
			response.save()
			response.submit()
		except Exception as e:
			print(e)
			pass

	# print("After Creating Return DN ",datetime.datetime.now())



def prepare_closeable_dn(all_dns):
	#check return / submit / cancel qty

	grouper = itemgetter("parent", "so_detail")
	result = []
	# grouping for individual deliver note items

	for key, grp in groupby(sorted(all_dns, key = grouper), grouper):
		temp_dict = dict(zip(["parent", "so_detail"], key))
		procesed_qty = 0

		actual_qty = 0
		for item in grp:
			_qty = -1* item.get("qty") if item.get("qty")<0 else item.get("qty")
			procesed_qty+=1
			actual_qty = item.get("act_qty")

		temp_dict["procesed_qty"] = procesed_qty
		temp_dict['actual_qty']	= actual_qty
		result.append(temp_dict)

	# grouping for individual deliver note
	grouper = itemgetter("parent")
	closeable_dns = []
	for key, grp in groupby(sorted(result, key = grouper), grouper):
		temp_dict = dict(zip(["parent"], [key]))
		temp_dict["closeable"] = True

		for item in grp:
			if  item.get("procesed_qty") < item.get("actual_qty"):
				temp_dict["closeable"] = False

		closeable_dns.append(temp_dict)

	
	closeable_dn={}
	for dn in closeable_dns:
		if dn.get("closeable"):
			closeable_dn.update({dn.get("parent"):dn.get("closeable")})

	######old logic  Based on single Grain decider Method
	# qty_check={}
	# closeable_dn  = {}
	# for dn in all_dns:
	# 	_qty = -1* dn.get("qty") if dn.get("qty")<0 else dn.get("qty")

	# 	if qty_check.get(dn.get("parent")):
	# 		qty = qty_check.get(dn.get("parent"))+_qty
	# 		qty_check.update({dn.get("parent"):qty})
	# 	else:
	# 		qty_check.update({dn.get("parent"):_qty})

	# for dn in all_dns:
	# 	if dn.get("parent") in qty_check and dn.get("parent") not in closeable_dn:
	# 		act_qty = dn.get("act_qty")
	# 		procesed_qty = qty_check.get(dn.get("parent"))
	# 		if procesed_qty >= act_qty:
	# 			closeable_dn.update({dn.get("parent"):procesed_qty})

	return closeable_dn


@frappe.whitelist()
def get_closeable_dn(doc):
	doc = json.loads(doc)
	from_date = doc.get("from_date")
	to_date = doc.get("to_date")
	all_dns = frappe.db.sql(""" select dni.parent,si.docstatus,sii.qty,si.name,
	 			si.status,dni.qty as act_qty,sii.so_detail
	 		from `tabDelivery Note Item` dni 
	 			left join `tabSales Invoice Item` sii on sii.delivery_note = dni.parent 
	 			left join `tabSales Invoice` si on sii.parent= si.name 
	 			left join `tabDelivery Note` dn on dn.name = dni.parent
	 			where si.docstatus>0  and si.status!='Credit Note Issued' 
	 			and dn.status = 'To Bill' 
	 			and date(dn.posting_date) between '{0}' and '{1}' """.format(from_date,to_date),as_dict=1)

	print(all_dns,"===")


	closeable_dn=prepare_closeable_dn(all_dns)
	closeable_dn = {}
	to_bill_closeable = get_to_bill_closeable_dn(from_date,to_date)
	print(to_bill_closeable,"====closeable_dn")
	closeable_dn.update(to_bill_closeable)
	return closeable_dn


def get_to_bill_closeable_dn(from_date,to_date):
	all_dns = frappe.db.sql(""" select distinct dni.parent
			from `tabDelivery Note Item` dni  
				left join `tabDelivery Note` dn on dn.name = dni.parent 
				where dn.docstatus>0 
				and dn.status = 'To Bill' and is_return = 0
				and date(dn.posting_date) between '{0}' and '{1}'  """.format(from_date,to_date),as_dict=1)

	closeable = {}
	for dn in all_dns:

		try:
			make_sales_invoice(dn.get("parent"),None)
		except:
			closeable.update({dn.get("parent"):True})
	return closeable

@frappe.whitelist()
def close_delivery_notes(closeable_dn):
	#close the closeable delivery notes
	print(closeable_dn,"===")
	closeable_dn = json.loads(closeable_dn)
	for cdn in closeable_dn:
		dn = frappe.get_doc("Delivery Note", cdn)
		dn.update_status("Closed")
	return True



@frappe.whitelist()
def make_sales_invoice(source_name, target_doc=None):
	doc = frappe.get_doc('Delivery Note', source_name)

	to_make_invoice_qty_map = {}
	returned_qty_map = get_returned_qty_map(source_name)
	invoiced_qty_map = get_invoiced_qty_map(source_name)

	def set_missing_values(source, target):
		target.ignore_pricing_rule = 1
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")

		if len(target.get("items")) == 0:
			frappe.throw(_("All these items have already been invoiced"))

		target.run_method("calculate_taxes_and_totals")

		# set company address
		if source.company_address:
			target.update({'company_address': source.company_address})
		else:
			# set company address
			target.update(get_company_address(target.company))

		if target.company_address:
			target.update(get_fetch_values("Sales Invoice", 'company_address', target.company_address))

	def update_item(source_doc, target_doc, source_parent):
		target_doc.qty = to_make_invoice_qty_map[source_doc.name]

		if source_doc.serial_no and source_parent.per_billed > 0:
			target_doc.serial_no = get_delivery_note_serial_no(source_doc.item_code,
				target_doc.qty, source_parent.name)

	def get_pending_qty(item_row):
		pending_qty = item_row.qty - invoiced_qty_map.get(item_row.name, 0)

		returned_qty = 0
		if returned_qty_map.get(item_row.item_code, 0) > 0:
			returned_qty = flt(returned_qty_map.get(item_row.item_code, 0))
			returned_qty_map[item_row.item_code] -= pending_qty

		if returned_qty:
			if returned_qty >= pending_qty:
				pending_qty = 0
				returned_qty -= pending_qty
			else:
				pending_qty -= returned_qty
				returned_qty = 0

		to_make_invoice_qty_map[item_row.name] = pending_qty

		return pending_qty

	doc = get_mapped_doc("Delivery Note", source_name, {
		"Delivery Note": {
			"doctype": "Sales Invoice",
			"field_map": {
				"is_return": "is_return"
			},
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Delivery Note Item": {
			"doctype": "Sales Invoice Item",
			"field_map": {
				"name": "dn_detail",
				"parent": "delivery_note",
				"so_detail": "so_detail",
				"against_sales_order": "sales_order",
				"serial_no": "serial_no",
				"cost_center": "cost_center"
			},
			"postprocess": update_item,
			"filter": lambda d: get_pending_qty(d) <= 0 if not doc.get("is_return") else get_pending_qty(d) > 0
		},
		"Sales Taxes and Charges": {
			"doctype": "Sales Taxes and Charges",
			"add_if_empty": True
		},
		"Sales Team": {
			"doctype": "Sales Team",
			"field_map": {
				"incentives": "incentives"
			},
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)

	return doc



def get_returned_qty_map(delivery_note):
	"""returns a map: {so_detail: returned_qty}"""
	returned_qty_map = frappe._dict(frappe.db.sql("""select dn_item.item_code, sum(abs(dn_item.qty)) as qty
		from `tabDelivery Note Item` dn_item, `tabDelivery Note` dn
		where dn.name = dn_item.parent
			and dn.docstatus = 1
			and dn.is_return = 1
			and dn.return_against = %s
		group by dn_item.item_code
	""", delivery_note))

	return returned_qty_map



def get_invoiced_qty_map(delivery_note):
	"""returns a map: {dn_detail: invoiced_qty}"""
	invoiced_qty_map = {}

	for dn_detail, qty in frappe.db.sql("""select dn_detail, qty from `tabSales Invoice Item`
		where delivery_note=%s and docstatus=1""", delivery_note):
			if not invoiced_qty_map.get(dn_detail):
				invoiced_qty_map[dn_detail] = 0
			invoiced_qty_map[dn_detail] += qty

	return invoiced_qty_map
