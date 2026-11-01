import base64
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from invento_print.ticket import build_bill, build_test_ticket, build_ticket
from ury.ury.api import ury_print
from ury.ury_pos.api import getBranch

KOT_CATCH_UP_HOURS = 12
# A bill printed hours late is no use to anyone at the table, unlike a KOT record.
BILL_CATCH_UP_HOURS = 2
BATCH_SIZE = 10
ALLOWED_WIDTHS = (32, 48)
PAGE_ALIVE_SECONDS = 30


def _require_access():
	if frappe.session.user == "Guest" or not frappe.has_permission("URY KOT", "read"):
		frappe.throw(_("Not permitted to print"), frappe.PermissionError)
	return getBranch()


def _encode(ticket):
	return base64.b64encode(ticket).decode("ascii")


def _width(width):
	width = int(width)
	if width not in ALLOWED_WIDTHS:
		frappe.throw(_("Unsupported paper width"))
	return width


def _page_key(branch):
	return f"invento_print_page_alive:{branch}"


def _pending_kots(branch, since, width):
	start = max(get_datetime(since), now_datetime() - timedelta(hours=KOT_CATCH_UP_HOURS))
	kot = frappe.qb.DocType("URY KOT")
	log = frappe.qb.DocType("KOT Print Log")
	names = (
		frappe.qb.from_(kot)
		.left_join(log)
		.on(log.kot == kot.name)
		.select(kot.name)
		.where(kot.docstatus == 1)
		.where(kot.branch == branch)
		.where(kot.creation >= start)
		.where(log.name.isnull())
		.orderby(kot.creation)
		.limit(BATCH_SIZE)
		.run(pluck=True)
	)
	tickets = []
	for name in names:
		doc = frappe.get_doc("URY KOT", name)
		kot = doc.as_dict()
		invoice_details = frappe.db.get_value("POS Invoice", doc.invoice, ["mobile_number", "order_type"], as_dict=True) or {}
		kot.update(invoice_details)
		tickets.append(
			{
				"kind": "kot",
				"id": name,
				"label": " - ".join(filter(None, [name, doc.restaurant_table, doc.type])),
				"ticket": _encode(build_ticket(kot, width)),
			}
		)
	return tickets


def _company_details(invoice):
	company = frappe.db.get_value("Company", invoice.company, ["company_name", "phone_no", "tax_id"], as_dict=True)
	details = {"name": company.company_name, "phone": company.phone_no, "tax_id": company.tax_id, "address_lines": []}

	address_name = frappe.db.get_value("POS Profile", invoice.pos_profile, "company_address")
	if address_name:
		address = frappe.get_doc("Address", address_name)
		city = " ".join(filter(None, [address.city, address.pincode]))
		details["address_lines"] = list(filter(None, [address.address_line1, address.address_line2, city]))
		details["phone"] = address.phone or details["phone"]
		details["tax_id"] = address.get("gstin") or details["tax_id"]
	return details


def _pending_bills(branch, width):
	start = now_datetime() - timedelta(hours=BILL_CATCH_UP_HOURS)
	jobs = frappe.get_all(
		"Bill Print Job",
		filters={"status": "Pending", "branch": branch, "creation": [">=", start]},
		fields=["name", "invoice"],
		order_by="creation",
		limit=BATCH_SIZE,
	)
	tickets = []
	for job in jobs:
		invoice = frappe.get_doc("POS Invoice", job.invoice)
		tickets.append(
			{
				"kind": "bill",
				"id": job.name,
				"label": " - ".join(filter(None, ["Bill", invoice.name, invoice.restaurant_table])),
				"ticket": _encode(build_bill(invoice.as_dict(), _company_details(invoice), width)),
			}
		)
	return tickets


@frappe.whitelist()
def get_pending_tickets(since, width=48):
	"""Return what the laptop page should print next, oldest first, as ready-to-print tickets."""
	branch = _require_access()
	width = _width(width)
	frappe.cache.set_value(_page_key(branch), 1, expires_in_sec=PAGE_ALIVE_SECONDS)
	return _pending_kots(branch, since, width) + _pending_bills(branch, width)


@frappe.whitelist(methods=["POST"])
def mark_printed(kind, id, printer=None):
	branch = _require_access()
	if kind == "kot":
		if frappe.db.get_value("URY KOT", id, "branch") != branch:
			frappe.throw(_("Not permitted to print this KOT"), frappe.PermissionError)
		if not frappe.db.exists("KOT Print Log", id):
			frappe.get_doc(
				{"doctype": "KOT Print Log", "kot": id, "printer": printer, "printed_by": frappe.session.user}
			).insert(ignore_permissions=True, ignore_if_duplicate=True)
	elif kind == "bill":
		if frappe.db.get_value("Bill Print Job", id, "branch") != branch:
			frappe.throw(_("Not permitted to print this bill"), frappe.PermissionError)
		frappe.db.set_value("Bill Print Job", id, {"status": "Printed", "printer": printer})
	else:
		frappe.throw(_("Unknown print type"))


@frappe.whitelist()
def get_test_ticket(printer, width=48):
	_require_access()
	return _encode(build_test_ticket(printer, _width(width)))


def _queue_bill(invoice_name):
	invoice = frappe.get_doc("POS Invoice", invoice_name)
	if not frappe.has_permission("POS Invoice", "write", doc=invoice):
		frappe.throw(_("Not permitted to print this invoice"), frappe.PermissionError)

	# Staff must find out now if nothing can print, not when the customer is waiting for the bill.
	if not frappe.cache.get_value(_page_key(invoice.branch), expires=True):
		frappe.throw(
			_("The bill was not printed. Open the KOT Printer page on the laptop and check it says Ready.")
		)

	if not frappe.db.exists("Bill Print Job", {"invoice": invoice_name, "status": "Pending"}):
		frappe.get_doc(
			{
				"doctype": "Bill Print Job",
				"invoice": invoice_name,
				"branch": invoice.branch,
				"requested_by": frappe.session.user,
			}
		).insert(ignore_permissions=True)

	# Keeps URY's own steps for a printed bill: marks it printed and frees the table.
	ury_print.qz_print_update(invoice_name)
	return "Success"


@frappe.whitelist()
def network_printing(doctype, name, printer_setting, print_format=None, doc=None, no_letterhead=0):
	if doctype != "POS Invoice":
		return ury_print.network_printing(doctype, name, printer_setting, print_format, doc, no_letterhead)
	return _queue_bill(name)


@frappe.whitelist()
def select_network_printer(pos_profile, invoice_id, print_format=None):
	return _queue_bill(invoice_id)
