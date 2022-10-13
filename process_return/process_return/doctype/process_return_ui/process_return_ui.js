// Copyright (c) 2020, AK and contributors
// For license information, please see license.txt

frappe.ui.form.on('Process Return UI', {
	// refresh: function(frm) {

	// }
	get_records:function(frm){
		if (frm.doc.type == "Return Delivery Notes"){
			frm.trigger("fetch_si_records")
		}

		if (frm.doc.type == "Close Delivery Notes"){
			frm.trigger("fetch_closable_dn")
		}
		
	},
	fetch_si_records:function(frm){
		frappe.call({
			method:"process_return.process_return.doctype.process_return_ui.process_return_ui.get_return_invoice",
			args: {
					doc:frm.doc
				},
			freeze: true,
			freeze_message: __("Processing"),
			callback: function (r) {
				frm.events.prepare_and_render_html(frm,r.message,"retrun_inv")
			}
		})

	},

	fetch_closable_dn:function(frm){

			frappe.call({
			method:"process_return.process_return.doctype.process_return_ui.process_return_ui.get_closeable_dn",
			args: {
					doc:frm.doc
				},
			freeze: true,
			freeze_message: __("Processing"),
			callback: function (r) {
					var records = []
					console.log(r.message);
					$.each(r.message,function(k,v){
						records.push(k)
					})
					frm.events.prepare_and_render_html(frm,records,"delivery_notes")
			}
		})

	},

	prepare_and_render_html:function(frm,records,type){
			var rec_html_wraper=frm.fields_dict.rec_html.$wrapper
			rec_html_wraper.html("")
			var html_line='';
			$.each(records, function(i,inv) {
				
				if (i===0 || (i % 4) === 0) {
					html_line = $('<div class="row"></div>').appendTo(rec_html_wraper);
				}
				$(repl('<div class="col-xs-6 return-invoice-checkbox">\
					<div class="checkbox">\
					<label><input type="checkbox" class="%(rec_type)s" %(rec_type)s="%(rec_name)s" \
					checked=True/>\
					<b>%(rec_name)s </b></label>\
					</div></div>', {rec_name: inv,rec_type:type})).appendTo(html_line);
			})

	},

	return_delivery_notes:function(frm){

		var retrun_inv=[]

		var rec_html_wraper=frm.fields_dict.rec_html.$wrapper
		$.each(rec_html_wraper.find('.retrun_inv:checked'), function(i, act){
			retrun_inv.push($(this).attr('retrun_inv'))
		})

		frappe.call({
			method:"process_return.process_return.doctype.process_return_ui.process_return_ui.proceed_to_return_dn",
			args: {
					invoices:retrun_inv
				},
			freeze: true,
			freeze_message: __("Processing"),
			callback: function (r) {
				frm.trigger("fetch_si_records")
			}
		})


	},

	close_delivery_notes:function(frm){

		var closeable_dn=[]

		var rec_html_wraper=frm.fields_dict.rec_html.$wrapper
		$.each(rec_html_wraper.find('.delivery_notes:checked'), function(i, act){
			closeable_dn.push($(this).attr('delivery_notes'))
		})

		frappe.call({
			method:"process_return.process_return.doctype.process_return_ui.process_return_ui.close_delivery_notes",
			args: {
					closeable_dn:closeable_dn
				},
			freeze: true,
			freeze_message: __("Processing"),
			callback: function (r) {
				frm.trigger("fetch_closable_dn")
			}
		})

	},

	proceed_to_return:function(frm){

		
		if (frm.doc.type == "Return Delivery Notes"){
			frm.trigger("return_delivery_notes")
		}

		if (frm.doc.type == "Close Delivery Notes"){
			frm.trigger("close_delivery_notes")
		}
		

	}
});
