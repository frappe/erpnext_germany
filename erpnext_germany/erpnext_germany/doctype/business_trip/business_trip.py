# Copyright (c) 2024, ALYF GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _, get_installed_apps
from frappe.utils import formatdate


class BusinessTrip(Document):
	def before_save(self):
		self.set_regional_amount()
		self.set_whole_day_time()
		self.calculate_total()
		self.calculate_total_mileage_allowance()

	def validate(self):
		self.validate_from_to_dates("from_date", "to_date")

	def set_whole_day_time(self):
		for allowance in self.allowances:
			if allowance.whole_day:
				allowance.from_time = "00:00"
				allowance.to_time = "23:59"

	def set_regional_amount(self):
		if not self.region:
			return

		region = frappe.get_doc("Business Trip Region", self.region)
		whole_day = region.get("whole_day", 0.0)
		arrival_or_departure = region.get("arrival_or_departure", 0.0)
		accomodation = region.get("accomodation", 0.0)

		for allowance in self.allowances:
			amount = whole_day if allowance.whole_day else arrival_or_departure
			if allowance.breakfast_was_provided:
				amount -= whole_day * 0.2

			if allowance.lunch_was_provided:
				amount -= whole_day * 0.4

			if allowance.dinner_was_provided:
				amount -= whole_day * 0.4

			if not allowance.accommodation_was_provided:
				amount += accomodation

			allowance.amount = max(amount, 0.0)

	def calculate_total_mileage_allowance(self):
		self.total_mileage_allowance = sum(journey.distance for journey in self.journeys if journey.mode_of_transport == "Car (private)")*frappe.db.get_single_value("Business Trip Settings", "mileage_allowance")

	def calculate_total(self):
		self.total_allowance = sum(allowance.amount for allowance in self.allowances)

	def before_submit(self):
		self.status = "Submitted"

	def on_submit(self):
		if not self.allowances:
			return

		if "hrms" not in get_installed_apps():
			return

		# Create Expense Claim for Car (private) and Allowance
		expense_claim = frappe.new_doc("Expense Claim")
		expense_claim.update(
			{
				"employee": self.employee,
				"company": self.company,
				"posting_date": frappe.utils.today(),
				"business_trip": self.name,
				"project": self.project,
				"cost_center": self.cost_center,
			}
		)

		for journey in self.journeys:
			if journey.mode_of_transport == "Car (private)":
				description = f'{journey.distance}km * {frappe.db.get_single_value("Business Trip Settings", "mileage_allowance")}€/km von {getattr(journey, "from")} nach {journey.to} (Fahrt mit Privatauto)'
				
				expense_claim_type_car = frappe.db.get_single_value("Business Trip Settings", "expense_claim_type_car")
				
				expense_claim.append(
				"expenses",
				{
					"expense_date": journey.date,
					"expense_type": expense_claim_type_car,
					"description": description,
					"amount": journey.distance * frappe.db.get_single_value("Business Trip Settings", "mileage_allowance"),
					"sanctioned_amount": journey.distance * frappe.db.get_single_value("Business Trip Settings", "mileage_allowance"),
					"project": self.project,
					"cost_center": self.cost_center,
				},
			)
			else:
				journey.distance = 0

		for allowance in self.allowances:
			description = _("Full Day") if allowance.whole_day else _("Arrival/Departure")
			if not allowance.accommodation_was_provided and frappe.db.get_value(
				"Business Trip Region", self.region, "accommodation"
			):
				description += ", zzgl. Hotel"

			if allowance.breakfast_was_provided:
				description += ", abzügl. Frühstück"

			if allowance.lunch_was_provided:
				description += ", abzügl. Mittagessen"

			if allowance.dinner_was_provided:
				description += ", abzügl. Abendessen"

			expense_claim_type = frappe.db.get_single_value("Business Trip Settings", "expense_claim_type")

			expense_claim.append(
				"expenses",
				{
					"expense_date": allowance.date,
					"expense_type": expense_claim_type,
					"description": description,
					"amount": allowance.amount,
					"sanctioned_amount": allowance.amount,
					"project": self.project,
					"cost_center": self.cost_center,
				},
			)

		expense_claim.save()

		# Create Purchase Invoices for other bills
		for journey in self.journeys:
			if journey.mode_of_transport != "Car (private)":
				match journey.mode_of_transport:
					case "Car":
						standard_supplier = frappe.db.get_single_value("Business Trip Settings", "standard_supplier_car")
						standard_item = frappe.db.get_single_value("Business Trip Settings", "standard_item_car")
						standard_account = frappe.db.get_single_value("Business Trip Settings", "standard_account_car")
					case "Car (rental)":
						standard_supplier = frappe.db.get_single_value("Business Trip Settings", "standard_supplier_car_rental")
						standard_item = frappe.db.get_single_value("Business Trip Settings", "standard_item_car_rental")
						standard_account = frappe.db.get_single_value("Business Trip Settings", "standard_account_car_rental")
					case "Taxi":
						standard_supplier = frappe.db.get_single_value("Business Trip Settings", "standard_supplier_taxi")
						standard_item = frappe.db.get_single_value("Business Trip Settings", "standard_item_taxi")
						standard_account = frappe.db.get_single_value("Business Trip Settings", "standard_account_taxi")
					case "Bus":
						standard_supplier = frappe.db.get_single_value("Business Trip Settings", "standard_supplier_bus")
						standard_item = frappe.db.get_single_value("Business Trip Settings", "standard_item_bus")
						standard_account = frappe.db.get_single_value("Business Trip Settings", "standard_account_bus")
					case "Train":
						standard_supplier = frappe.db.get_single_value("Business Trip Settings", "standard_supplier_train")
						standard_item = frappe.db.get_single_value("Business Trip Settings", "standard_item_train")
						standard_account = frappe.db.get_single_value("Business Trip Settings", "standard_account_train")
					case "Airplane":
						standard_supplier = frappe.db.get_single_value("Business Trip Settings", "standard_supplier_airplane")
						standard_item = frappe.db.get_single_value("Business Trip Settings", "standard_item_airplane")
						standard_account = frappe.db.get_single_value("Business Trip Settings", "standard_account_airplane")
					case "Public Transport":
						standard_supplier = frappe.db.get_single_value("Business Trip Settings", "standard_supplier_public_transport")
						standard_item = frappe.db.get_single_value("Business Trip Settings", "standard_item_public_transport")
						standard_account = frappe.db.get_single_value("Business Trip Settings", "standard_account_public_transport")
					case _:
						standard_supplier = ""
						standard_item = ""
						standard_account = ""
				self.create_invoice("journey", journey, standard_supplier, standard_item, standard_account)

		for accommodation in self.accommodations:
			standard_supplier = frappe.db.get_single_value("Business Trip Settings", "standard_supplier_accommodation")
			standard_item = frappe.db.get_single_value("Business Trip Settings", "standard_item_accommodation")
			standard_account = frappe.db.get_single_value("Business Trip Settings", "standard_account_accommodation")
			self.create_invoice("accommodation", accommodation, standard_supplier, standard_item, standard_account)

	def create_invoice(self, invoice_type, invoice_topic, standard_supplier, standard_item, standard_account):
		if standard_supplier != "" and standard_item != "" and standard_account != "" and invoice_topic.receipt != None:
			purchase_invoice = frappe.new_doc("Purchase Invoice")
			purchase_invoice.update(
				{
					"supplier": standard_supplier,
					"company": self.company,
					"posting_date": frappe.utils.today(),
					"business_trip": self.name,
					"project": self.project,
					"cost_center": self.cost_center,
				}
			)
			purchase_invoice.append(
				"items",
				{
					"item_name": standard_item,
					"qty": "1",
					"rate": "0",
					"project": self.project,
					"cost_center": self.cost_center,
					"expense_account": standard_account
				},
			)
			purchase_invoice.save()
			copy_attachments_by_file_url(invoice_topic.receipt, self.name, purchase_invoice)
		else:
			if invoice_topic.receipt == None:
				frappe.msgprint("<b>" + _("Missing receipt:") + "</b>")
			else:
				frappe.msgprint("<b>" + _("Standard supplier, item or expense account not set:") + "</b>")
			if invoice_type == "journey":
					frappe.msgprint(_("- Purchase Invoice for {0} / {1} from {2} to {3} not created!").format(formatdate(invoice_topic.date),_(invoice_topic.mode_of_transport),getattr(invoice_topic, 'from'),getattr(invoice_topic, 'to')))
			if invoice_type == "accommodation":
				frappe.msgprint(_("- Purchase Invoice for accommodation in {0} from {1} to {2} not created!").format(invoice_topic.city,formatdate(invoice_topic.from_date),formatdate(invoice_topic.to_date)))

def copy_attachments_by_file_url(file_url, attached_to_name, target_doc):
    """
    Copy an attachment identified by file_url to the target document.

    Args:
        file_url (str): The URL of the file to be copied.
        target_doc (object): The target document to which the file should be attached.
    """
    # Get the file record associated with the given file_url
    attachments = frappe.get_all("File",
                                 filters={
                                     "file_url": file_url,
									 "attached_to_name": attached_to_name
                                 },
                                 fields=["name", "file_url", "file_name", "attached_to_doctype", "attached_to_name"])

    if not attachments:
        frappe.throw(f"No file found with URL: {file_url}")

    for attachment in attachments:
        new_file = frappe.get_doc({
            "doctype": "File",
            "file_url": attachment.file_url,
            "file_name": attachment.file_name,
            "attached_to_doctype": target_doc.doctype,
            "attached_to_name": target_doc.name
        })
        new_file.insert()
        break

