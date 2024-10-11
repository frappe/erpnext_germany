# Copyright (c) 2024, ALYF GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import get_installed_apps


class BusinessTrip(Document):
	def before_save(self):
		self.set_regional_amount()
		self.calculate_total()

	def validate(self):
		self.validate_from_to_dates("from_date", "to_date")

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

	def calculate_total(self):
		self.total_allowance = sum(allowance.amount for allowance in self.allowances)

	def before_submit(self):
		self.status = "Submitted"

	def on_submit(self):
		if not self.allowances:
			return

		if "hrms" not in get_installed_apps():
			return

		expense_claim = frappe.new_doc("Expense Claim")
		expense_claim.update(
			{
				"employee": self.employee,
				"company": self.company,
				"posting_date": frappe.utils.today(),
				"business_trip": self.name,
				"project": self.project,
			}
		)

		for allowance in self.allowances:
			description = "Ganztägig" if allowance.whole_day else "An-/Abreise"
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

			expense_claim.append(
				"expenses",
				{
					"expense_date": allowance.date,
					"expense_type": "Additional meal expenses",
					"description": description,
					"amount": allowance.amount,
					"sanctioned_amount": allowance.amount,
				},
			)

		expense_claim.save()
