app_name = "invento_print"
app_title = "Invento Print"
app_publisher = "Invento"
app_description = "Prints URY KOTs from the restaurant laptop through QZ Tray"
app_email = "rgrahul1998@gmail.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["ury"]

# The POS sends bills to these methods when a bill printer is set on its POS Profile. Bills are
# queued here instead of going through CUPS, and the laptop's /kot-printer page prints them.
override_whitelisted_methods = {
	"ury.ury.api.ury_print.network_printing": "invento_print.api.network_printing",
	"ury.ury.api.ury_print.select_network_printer": "invento_print.api.select_network_printer",
}

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "invento_print",
# 		"logo": "/assets/invento_print/logo.png",
# 		"title": "Invento Print",
# 		"route": "/invento_print",
# 		"has_permission": "invento_print.api.permission.has_app_permission",
# 	}
# ]

# The dock, the rail down the left of the desk, is a document rather than a hook. Author it in
# Manage Dock on a developer-mode site and press Export to App, and it is written to
# `invento_print/dock/invento_print/invento_print.json` for git to carry. An app that ships none has no
# rail: its sidebar gets a switcher in the header instead.
#
# A companion app, one that extends a host app rather than standing on its own, says so with
# `mount_on` on that same record, and its entries are appended to the host's rail. Mounting keeps
# the companion off the apps screen, so it takes precedence over any add_to_apps_screen above.

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/invento_print/css/invento_print.css"
# app_include_js = "/assets/invento_print/js/invento_print.js"

# include js, css files in header of web template
# web_include_css = "/assets/invento_print/css/invento_print.css"
# web_include_js = "/assets/invento_print/js/invento_print.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "invento_print/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_kanban_js = {"doctype" : "public/js/doctype_kanban.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "invento_print/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "invento_print.utils.jinja_methods",
# 	"filters": "invento_print.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "invento_print.install.before_install"
# after_install = "invento_print.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "invento_print.uninstall.before_uninstall"
# after_uninstall = "invento_print.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "invento_print.utils.before_app_install"
# after_app_install = "invento_print.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "invento_print.utils.before_app_uninstall"
# after_app_uninstall = "invento_print.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "invento_print.build.after_build"

# To hook into the build process of other apps
# The list of apps being built is passed as an argument

# after_app_build = "invento_print.build.after_app_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "invento_print.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["invento_print.search.awesomebar_results"]

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
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"invento_print.tasks.all"
# 	],
# 	"daily": [
# 		"invento_print.tasks.daily"
# 	],
# 	"hourly": [
# 		"invento_print.tasks.hourly"
# 	],
# 	"weekly": [
# 		"invento_print.tasks.weekly"
# 	],
# 	"monthly": [
# 		"invento_print.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "invento_print.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "invento_print.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "invento_print.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "invento_print.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["invento_print.utils.before_request"]
# after_request = ["invento_print.utils.after_request"]

# Job Events
# ----------
# before_job = ["invento_print.utils.before_job"]
# after_job = ["invento_print.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"invento_print.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

