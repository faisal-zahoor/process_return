# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "process_return"
app_title = "Process Return"
app_publisher = "AK"
app_description = "Process Return"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "ajadhao753@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/process_return/css/process_return.css"
# app_include_js = "/assets/process_return/js/process_return.js"

# include js, css files in header of web template
# web_include_css = "/assets/process_return/css/process_return.css"
# web_include_js = "/assets/process_return/js/process_return.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "process_return.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "process_return.install.before_install"
# after_install = "process_return.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "process_return.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }





doc_events = {
    

    "Sales Invoice":{
        "validate":"process_return.process_return.custom_script.sales_invoice.sales_invoice.custom_validate",
#        "on_submit":"process_return.process_return.custom_script.sales_invoice.sales_invoice.custom_submit",
    },

    "Delivery Note":{
        "validate":"process_return.process_return.custom_script.delivery_note.delivery_note.custom_validate",
        "on_update_after_submit":"process_return.process_return.custom_script.delivery_note.delivery_note.custom_update",
    },

    
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"process_return.tasks.all"
# 	],
# 	"daily": [
# 		"process_return.tasks.daily"
# 	],
# 	"hourly": [
# 		"process_return.tasks.hourly"
# 	],
# 	"weekly": [
# 		"process_return.tasks.weekly"
# 	]
# 	"monthly": [
# 		"process_return.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "process_return.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "process_return.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "process_return.task.get_dashboard_data"
# }

