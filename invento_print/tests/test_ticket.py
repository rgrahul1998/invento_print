import unittest

from invento_print.ticket import CUT, build_bill, build_test_ticket, build_ticket

CONTROL_CODES = (b"\x1b@", b"\x1ba\x00", b"\x1ba\x01", b"\x1d!\x00", b"\x1d!\x01", b"\x1d!\x11", b"\x1bE\x00", b"\x1bE\x01", CUT)


def plain_lines(ticket):
	for code in CONTROL_CODES:
		ticket = ticket.replace(code, b"")
	return ticket.split(b"\n")


def kot(**overrides):
	base = {
		"name": "KOT-00001",
		"type": "New Order",
		"production": "Kitchen",
		"restaurant_table": "T11",
		"table_takeaway": 0,
		"order_no": "42",
		"invoice": "UDT-SA-00001",
		"customer_name": "Avijit",
		"mobile_number": "2222222222",
		"order_type": "Dine In",
		"user": "Cashier",
		"date": "2026-11-01",
		"time": "14:32:10.123",
		"comments": "",
		"kot_items": [{"item": "PHU", "item_name": "Phulka", "quantity": "2", "comments": "less oil"}],
	}
	base.update(overrides)
	return base


def bill(**overrides):
	base = {
		"name": "UDT-SA-00001",
		"company": "Invento",
		"docstatus": 0,
		"posting_date": "2026-11-01",
		"posting_time": "14:32:10.5",
		"restaurant_table": "T11",
		"order_type": "Dine In",
		"custom_ury_order_number": "437",
		"customer_name": "Avijit",
		"mobile_number": "2222222222",
		"total": 1000,
		"discount_amount": 100,
		"rounding_adjustment": 0.5,
		"grand_total": 944.5,
		"rounded_total": 945,
		"paid_amount": 1000,
		"items": [
			{"item_name": "Phulka", "qty": 2, "rate": 50, "amount": 100},
			{"item_name": "Malgudi Paneer & Veg Biryani with Raita, extra spicy", "qty": 2, "rate": 450, "amount": 900},
		],
		"taxes": [{"description": "CGST 2.5%", "tax_amount": 22.5}, {"description": "SGST 2.5%", "tax_amount": 22}],
		"payments": [{"mode_of_payment": "Cash", "amount": 1000}, {"mode_of_payment": "UPI", "amount": 0}],
		"change_amount": 55,
	}
	base.update(overrides)
	return base


class TestKot(unittest.TestCase):
	def test_contains_order_details_and_cuts(self):
		ticket = build_ticket(kot())
		for text in (b"KOT", b"Name: Avijit", b"Tel#: 2222222222", b"No: #UDT-SA-00001", b"14:32:10", b"01/11/2026",
			b"Bill No: #42", b"Dine In", b"Table No: T11", b"ITEM", b"QTY", b"Phulka", b"X 2", b"* less oil", b"Kitchen"):
			self.assertIn(text, ticket)
		self.assertTrue(ticket.endswith(CUT))

	def test_changed_orders_are_labelled_and_new_orders_are_not(self):
		self.assertNotIn(b"MODIFIED", build_ticket(kot()))
		for kot_type, title in (
			("Order Modified", b"ORDER MODIFIED"),
			("Cancelled", b"CANCELLED"),
			("Partially cancelled", b"PARTLY CANCELLED"),
			("Duplicate", b"REPRINT"),
		):
			self.assertIn(title, build_ticket(kot(type=kot_type)))

	def test_takeaway_has_no_table(self):
		ticket = build_ticket(kot(restaurant_table="T1", table_takeaway=1, order_type=None))
		self.assertIn(b"Takeaway", ticket)
		self.assertNotIn(b"Table No", ticket)
		self.assertIn(b"Takeaway", build_ticket(kot(restaurant_table=None, order_type=None)))

	def test_cancelled_quantity_shows_old_and_new(self):
		self.assertIn(b"5 > 3", build_ticket(kot(kot_items=[{"item_name": "Phulka", "quantity": "5", "cancelled_qty": "2"}])))

	def test_lines_fit_paper_width(self):
		name = "Malgudi Paneer & Veg Biryani with Raita " * 2
		for width in (32, 48):
			ticket = build_ticket(kot(kot_items=[{"item_name": name, "quantity": "1", "comments": name}], comments=name), width)
			for line in plain_lines(ticket):
				self.assertLessEqual(len(line), width, line)

	def test_staff_text_cannot_inject_printer_commands(self):
		ticket = build_ticket(kot(comments="hi\x1b@\x1dV\x01there", customer_name="a\x1b@", kot_items=[{"item_name": "Tea\x1b@", "quantity": "1"}]))
		self.assertEqual(ticket.count(b"\x1b@"), 1)
		self.assertEqual(ticket.count(CUT), 1)

	def test_non_ascii_text_does_not_crash(self):
		self.assertIn(b"Ch?y", build_ticket(kot(kot_items=[{"item_name": "Chäy", "quantity": "1"}])))

	def test_missing_values_are_safe(self):
		self.assertTrue(build_ticket({"name": "KOT-1"}).endswith(CUT))

	def test_test_ticket_names_printer(self):
		self.assertIn(b"RETSOL", build_test_ticket("RETSOL"))


class TestBill(unittest.TestCase):
	def test_contains_header_order_and_totals(self):
		ticket = build_bill(bill(), {"name": "Invento Cafe", "address_lines": ["1 MG Road"], "phone": "98765", "tax_id": "29ABC"})
		for text in (b"Invento Cafe", b"1 MG Road", b"Phone: 98765", b"GSTIN: 29ABC", b"Name: Avijit", b"Tel#: 2222222222",
			b"No: #UDT-SA-00001", b"Bill No: #437", b"Dine In", b"Table No: T11", b"PRICE", b"Phulka", b"X 2", b"Rs.100.00",
			b"Item Sub Total", b"Rs.1,000.00", b"Discount", b"-Rs.100.00", b"CGST 2.5%", b"Rs.22.50", b"Round Off", b"Total", b"Rs.945.00",
			b"Thank You. Visit Again.", b"THIS IS COMPUTER GENERATED INVOICE"):
			self.assertIn(text, ticket)
		self.assertNotIn(b"NO REFUND", ticket)
		self.assertTrue(ticket.endswith(CUT))

	def test_gst_details_only_print_once_set_up(self):
		without_gst = build_bill(bill(taxes=[]), {"name": "Invento"})
		self.assertNotIn(b"GSTIN", without_gst)
		self.assertNotIn(b"CGST", without_gst)

		with_gst = build_bill(bill(), {"name": "Invento", "tax_id": "27ABCDE1234F1Z5"})
		for text in (b"GSTIN: 27ABCDE1234F1Z5", b"CGST 2.5%", b"SGST 2.5%", b"Rs.22.50", b"Rs.22.00"):
			self.assertIn(text, with_gst)

	def test_payment_details_only_on_paid_bills(self):
		draft = build_bill(bill())
		self.assertNotIn(b"M.O.P", draft)
		self.assertNotIn(b"Paid", draft)
		self.assertNotIn(b"Change", draft)
		paid = build_bill(bill(docstatus=1))
		self.assertIn(b"M.O.P: Cash\n", paid)
		self.assertIn(b"Paid", paid)
		self.assertIn(b"Change", paid)
		self.assertNotIn(b"UPI", paid)

	def test_lines_fit_paper_width(self):
		for width in (32, 48):
			for line in plain_lines(build_bill(bill(docstatus=1), {"name": "Invento"}, width)):
				self.assertLessEqual(len(line), width, line)

	def test_merged_bill_shows_both_and_combined_total(self):
		ticket = build_bill(bill(custom_merged_pos_invoice="UDT-SA-00002", custom_merged_total=500,
			custom_merged_pos_invoice_details=[{"item_name": "Dal", "qty": 1, "rate": 500, "amount": 500}]))
		for text in (b"Merged Bill: #UDT-SA-00002", b"Dal", b"This Bill", b"Rs.1,445.00"):
			self.assertIn(text, ticket)

	def test_staff_text_cannot_inject_printer_commands(self):
		ticket = build_bill(bill(customer_name="x\x1b@\x1dV\x01y"))
		self.assertEqual(ticket.count(b"\x1b@"), 1)
		self.assertEqual(ticket.count(CUT), 1)

	def test_missing_values_are_safe(self):
		self.assertTrue(build_bill({"name": "X"}).endswith(CUT))
