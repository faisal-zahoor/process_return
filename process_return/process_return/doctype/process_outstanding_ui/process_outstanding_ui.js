// Copyright (c) 2020, AK and contributors
// For license information, please see license.txt

frappe.ui.form.on('Process Outstanding UI', {
	// refresh: function(frm) {

	// },
	get_invoices:function(frm){

		frappe.call({
				method: "process_return.process_return.doctype.process_outstanding_ui.process_outstanding_ui.get_neg_outstatnding_invoices",
				args: {
					params:{company: frm.doc.company,
							party_type: "Customer",
							party: frm.doc.customer,
							date: frm.doc.from_date,
							cost_center: ""},
					
					doc:frm.doc
				},
				callback: function(r, rt) {
					
					var rec_html_wraper=frm.fields_dict.rec_html.$wrapper
					rec_html_wraper.html("")
					var html_line='';
					$.each(r.message, function(i,inv) {
						
						if (i===0 || (i % 4) === 0) {
							html_line = $('<div class="row"></div>').appendTo(rec_html_wraper);
						}
						$(repl('<div class="col-xs-6 neg-invoice-checkbox">\
							<div class="checkbox">\
							<label><input type="checkbox" class="neg_out_inv" neg_out_inv="%(rec_name)s" \
							checked=True/>\
							<b>%(rec_name)s </b></label>\
							</div></div>', {rec_name: inv})).appendTo(html_line);
					})

				}

		})
	},

	make_jv:function(frm){
		var neg_out_inv=[]

		var rec_html_wraper=frm.fields_dict.rec_html.$wrapper
		$.each(rec_html_wraper.find('.neg_out_inv:checked'), function(i, act){
			neg_out_inv.push($(this).attr('neg_out_inv'))
		})

		frappe.call({
			method:"process_return.process_return.doctype.process_outstanding_ui.process_outstanding_ui.make_jv_for_invs",
			args: {
					invoices:neg_out_inv,
					params:{company: frm.doc.company,
							party_type: "Customer",
							party: frm.doc.customer,
							date: frm.doc.from_date,
							cost_center: ""},
					
					doc:frm.doc
				},
			freeze: true,
			freeze_message: __("Processing"),
			callback: function (r) {

				frappe.msgprint(__("Following Entries Created {0} ", [JSON.stringify(r.message)]));
			}
		})
	}
});
