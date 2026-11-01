import frappe

LAPTOP_PRINTER = "Laptop Thermal Printer"


def enable_laptop_bills(pos_profile):
	"""Point a POS Profile's bills at the laptop page. Run with `bench execute`.

	The POS only sends bills to the server when a bill printer is set, so this adds a placeholder
	printer. Its address is never used, because invento_print.api handles the bill instead.
	"""
	if not frappe.db.exists("Network Printer Settings", LAPTOP_PRINTER):
		printer = frappe.new_doc("Network Printer Settings")
		printer.name = LAPTOP_PRINTER
		printer.server_ip = "localhost"
		printer.port = 631
		printer.printer_name = LAPTOP_PRINTER
		printer.insert(set_name=LAPTOP_PRINTER)

	profile = frappe.get_doc("POS Profile", pos_profile)
	if not any(row.printer == LAPTOP_PRINTER for row in profile.printer_settings):
		profile.append("printer_settings", {"printer": LAPTOP_PRINTER, "bill": 1})
		profile.save()
	frappe.db.commit()
	return [(row.printer, row.bill) for row in profile.printer_settings]
