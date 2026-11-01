import frappe
from frappe import _
from frappe.utils import now

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/kot-printer"
		raise frappe.Redirect

	if not frappe.has_permission("URY KOT", "read"):
		frappe.throw(_("You need a URY role to print KOTs"), frappe.PermissionError)

	context.no_header = 1
	context.no_breadcrumbs = 1
	context.csrf_token = frappe.sessions.get_csrf_token()
	context.server_now = now()
