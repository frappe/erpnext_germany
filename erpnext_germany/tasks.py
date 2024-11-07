import frappe
from erpnext import get_default_company
from frappe.query_builder import DocType
from pypika import Interval
from pypika import functions as fn


def all():
	check_some_parties()


def get_customers(batch_size=4):
	"""Return a list of n customers who didn't have their VAT ID checked in the last 3 months."""
	customers = DocType("Customer")
	last_check = get_last_check_query("Customer")

	return (
		frappe.qb.from_(customers)
		.left_join(last_check)
		.on(customers.name == last_check.party)
		.select(
			fn.LiteralValue("'Customer'"),
			customers.name,
			customers.customer_name,
			customers.customer_primary_address,
			customers.tax_id,
		)
		.where(
			customers.tax_id.notnull()
			& (customers.disabled == 0)
			& (
				last_check.creation.isnull()
				| (last_check.creation < fn.Now() - Interval(months=3))
			)
		)
		.limit(batch_size)
		.run()
	)


def get_suppliers(batch_size=4):
	"""Return a list of n suppliers who didn't have their VAT ID checked in the last 3 months."""
	suppliers = DocType("Supplier")
	last_check = get_last_check_query("Supplier")

	return (
		frappe.qb.from_(suppliers)
		.left_join(last_check)
		.on(suppliers.name == last_check.party)
		.select(
			fn.LiteralValue("'Supplier'"),
			suppliers.name,
			suppliers.supplier_name,
			suppliers.supplier_primary_address,
			suppliers.tax_id,
		)
		.where(
			suppliers.tax_id.notnull()
			& (suppliers.disabled == 0)
			& (
				last_check.creation.isnull()
				| (last_check.creation < fn.Now() - Interval(months=3))
			)
		)
		.limit(batch_size)
		.run()
	)


def get_last_check_query(party_type: str):
	vat_id_checks = DocType("VAT ID Check")
	return (
		frappe.qb.from_(vat_id_checks)
		.select(
			vat_id_checks.party,
			fn.Max(vat_id_checks.creation).as_("creation"),
		)
		.where(
			(vat_id_checks.party_type == party_type)
			& (vat_id_checks.status.isin(["Completed", "Invalid Input"]))
		)
		.groupby(vat_id_checks.party)
	)


def check_some_parties():
	"""Check VAT IDs of customers who didn't have their VAT ID checked in the last 3 months."""
	requester_vat_id = None
	if company := get_default_company():
		requester_vat_id = frappe.get_cached_value("Company", company, "tax_id")

	for party_type, party, party_name, primary_address, vat_id in (
		get_customers() + get_suppliers()
	):
		doc = frappe.new_doc("VAT ID Check")
		doc.party_type = party_type
		doc.party = party
		doc.trader_name = party_name
		doc.party_vat_id = vat_id
		doc.company = company
		doc.requester_vat_id = requester_vat_id
		if primary_address:
			address = frappe.get_doc("Address", primary_address)
			doc.trader_street = address.address_line1
			doc.trader_postcode = address.pincode
			doc.trader_city = address.city

		doc.insert(ignore_permissions=True)
