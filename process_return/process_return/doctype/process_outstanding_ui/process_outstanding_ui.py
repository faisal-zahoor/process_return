# -*- coding: utf-8 -*-
# Copyright (c) 2020, AK and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json,erpnext
from erpnext.accounts.doctype.payment_entry.payment_entry import get_party_details
from erpnext.accounts.doctype.payment_entry.payment_entry import get_negative_outstanding_invoices
import datetime
from erpnext.accounts.utils import get_company_default
from frappe.utils import (add_days, getdate, formatdate, date_diff,
	add_years, get_timestamp, nowdate, flt, cstr, add_months, get_last_day)

class ProcessOutstandingUI(Document):
	pass

@frappe.whitelist()
def get_neg_outstatnding_invoices(doc,params):
	doc = json.loads(doc)
	params  = json.loads(params)

	party_details = get_party_details(**params)

	party_type = "Customer"
	party = party_details.get("party_name")
	party_account = party_details.get("party_account")
	party_account_currency = party_details.get("party_account_currency")
	company_currency = erpnext.get_company_currency(doc.get("company"))
	company = doc.get("company")

	neg_out_invs = get_negative_outstanding_invoices(party_type, 
												party, 
												party_account,
												company, 
												party_account_currency, 
												company_currency, cost_center=None)

	# neg_out_invs = [{'voucher_type': 'Sales Invoice', 
	# 				'voucher_no': 'EX/20-21-10010', 
	# 				'invoice_amount': 44.38, 
	# 				'outstanding_amount': 44.38, 
	# 				'posting_date': datetime.date(2020, 7, 26), 
	# 				'due_date': datetime.date(2020, 7, 26), 
	# 				'exchange_rate': 7.0}]

	from_date = doc.get("from_date")
	to_date = doc.get("to_date")
	neg_out_invs = [i.get('voucher_no') for i in neg_out_invs]
	invoices = [d.name for d in frappe.get_all("Sales Invoice", 
		filters={"posting_date": ["between", [from_date, to_date]],
				"name":["in",neg_out_invs]})]

	return invoices
	

@frappe.whitelist()
def make_jv_for_invs(invoices,params,doc):
	invoices  = json.loads(invoices)
	doc = json.loads(doc)
	params  = json.loads(params)

	party_details = get_party_details(**params)
	party_account = party_details.get("party_account")
	party = party_details.get("party_name")
	default_company = frappe.db.get_single_value('Global Defaults', 'default_company')
	cost_center = erpnext.get_default_cost_center(default_company)
	
	default_income_account =get_company_default(default_company,"default_income_account")
	
	default_receivable_account =get_company_default(default_company,"default_receivable_account")
	default_cash_account =get_company_default(default_company,"default_cash_account")

	created_ent = {}
	for inv in invoices:
		amount = frappe.db.get_value('Sales Invoice', inv,"outstanding_amount")
		amount = amount
		# make_journal_entry(default_receivable_account,company_account,amount,default_company,party,
		# 					inv,cost_center)
		pe = make_payment_entrys(default_receivable_account,default_cash_account,amount,default_company,party,
							inv,cost_center)
		
		created_ent.update({inv:pe})
	
	return created_ent


def make_payment_entrys(default_receivable_account, default_cash_account, amount,company,party, inv,cost_center=None, 
					posting_date=None, exchange_rate=1, 
					save=True, submit=False, project=None):
	
	pe = frappe.new_doc("Payment Entry")
	pe.posting_date = posting_date or nowdate()
	pe.company = company
	pe.payment_type = "Receive"
	pe.party_type = "Customer"
	pe.paid_from = default_receivable_account
	pe.paid_to = default_cash_account
	pe.mode_of_payment = "Cash"
	pe.party = party
	pe.paid_amount = amount
	pe.party_account = ''
	pe.received_amount = amount
	pe.append("references", {"reference_doctype":"Sales Invoice",
							"reference_name":inv,
							"allocated_amount":amount})

	pe.save()
	return pe.name

def make_journal_entry(account1, account2, amount,company,party, cost_center=None, 
					posting_date=None, exchange_rate=1, 
					save=True, submit=False, project=None):

	if not cost_center:
		cost_center = "_Test Cost Center - _TC"

	jv = frappe.new_doc("Journal Entry")
	jv.posting_date = posting_date or nowdate()
	jv.company = company
	jv.user_remark = "test"
	jv.multi_currency = 1
	jv.set("accounts", [
		{
			"account": account1,
			"cost_center": cost_center,
			"project": project,
			"debit_in_account_currency": amount if amount > 0 else 0,
			"credit_in_account_currency": abs(amount) if amount < 0 else 0,
			"exchange_rate": exchange_rate,
			"party_type":"Customer",
			"party":party
		}, {
			"account": account2,
			"cost_center": cost_center,
			"project": project,
			"credit_in_account_currency": amount if amount > 0 else 0,
			"debit_in_account_currency": abs(amount) if amount < 0 else 0,
			"exchange_rate": exchange_rate,
			"party_type":"Customer",
			"party":party
		}
	])
	if save or submit:
		jv.insert()

		if submit:
			jv.submit()

	return jv