from csv import DictReader

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from .custom_fields import get_custom_fields


def after_install():
	create_custom_fields(get_custom_fields())
	make_property_setters()
	import_data()
	insert_custom_records()


def import_data():
	for doctype, filename in (
		("Religious Denomination", "religious_denomination.csv"),
		("Employee Health Insurance", "employee_health_insurance.csv"),
		("Expense Claim Type", "expense_claim_type.csv"),
		("Business Trip Region", "business_trip_region.csv"),
	):
		if not frappe.db.exists("DocType", doctype):
			continue

		path = frappe.get_app_path("erpnext_germany", "data", filename)
		import_csv(doctype, path)


def import_csv(doctype, path):
	with open(path) as csvfile:
		reader = DictReader(csvfile)
		for row in reader:
			if frappe.db.exists(doctype, row):
				continue

			doc = frappe.new_doc(doctype)
			doc.update(row)
			doc.insert()


def make_property_setters():
	germany_property_setters = frappe.get_hooks("germany_property_setters")
	for doctypes, property_setters in germany_property_setters.items():
		if isinstance(doctypes, str):
			doctypes = (doctypes,)

		for doctype in doctypes:
			for property_setter in property_setters:
				for_doctype = not property_setter[0]
				make_property_setter(doctype, *property_setter, for_doctype)


def insert_custom_records():
	for custom_record in frappe.get_hooks("germany_custom_records"):
		filters = custom_record.copy()
		# Clean up filters. They need to be a plain dict without nested dicts or lists.
		for key, value in custom_record.items():
			if isinstance(value, (list, dict)):
				del filters[key]

		if not frappe.db.exists(filters):
			frappe.get_doc(custom_record).insert(ignore_if_duplicate=True)
