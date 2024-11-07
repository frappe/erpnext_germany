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

frappe.ui.form.on("Business Trip Allowance", {
    allowances_add(frm) {
		if (!frm.doc.from_date || !frm.doc.to_date || frm.doc.to_date < frm.doc.from_date) {
            frappe.msgprint(__('Please enter a correct start and end date of the trip!'));
            return;
        }
	
        if (frm.doc.allowances && frm.doc.allowances.length == 1) {
            let start = new Date(frm.doc.from_date);
			let end = new Date(frm.doc.to_date);

			frm.clear_table("allowances");

			for (let d = start; d <= end; d.setDate(d.getDate() + 1)) {
				let child = frm.add_child("allowances");
				let d_string = d.toISOString().slice(0, 10);
				frappe.model.set_value(child.doctype, child.name, "date", d_string);
			}

			frm.refresh_field("allowances");
        }
	},
});
