// Copyright (c) 2024, ALYF GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on("Business Trip", {
	setup(frm) {
		frm.set_query("employee", erpnext.queries.employee);
		frm.set_query("region", (doc) => {
			return {
				filters: {
					valid_from: ["<=", doc.from_date], 
				}
			};
		});
	},

	from_date: function (frm) {
		if (!frm.doc.to_date) {
			frm.set_value("to_date", frm.doc.from_date);
		}

		frm.fields_dict.to_date.datepicker.update({
			minDate: frm.doc.from_date ? new Date(frm.doc.from_date) : null,
		});
	},

	to_date: function (frm) {
		frm.fields_dict.from_date.datepicker.update({
			maxDate: frm.doc.to_date ? new Date(frm.doc.to_date) : null,
		});
	},
});

frappe.ui.form.on("Business Trip Journey", {
	journeys_add(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "date", frm.doc.from_date);
	},
});

frappe.ui.form.on("Business Trip Accommodation", {
	accommodations_add(frm, cdt, cdn) {
		frappe.model.set_value(cdt, cdn, "from_date", frm.doc.from_date);
		frappe.model.set_value(cdt, cdn, "to_date", frm.doc.to_date);
	},
});
