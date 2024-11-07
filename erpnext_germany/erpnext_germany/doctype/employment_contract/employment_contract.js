// Copyright (c) 2024, ALYF GmbH and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employment Contract", {
	refresh(frm) {
		if (frm.is_new() && !frm.doc.working_time_per_weekday?.length) {
			frm.trigger("prefill_working_days");
		}
	},
	distribute(frm) {
		if (!frm.doc.working_time_per_week) {
			frappe.show_alert(__("Please set the working time per week"));
		}

		if (!frm.doc.working_time_per_weekday?.length) {
			frm.trigger("prefill_working_days");
		}

		for (const row of frm.doc.working_time_per_weekday) {
			frappe.model.set_value(
				row.doctype,
				row.name,
				"working_time",
				frm.doc.working_time_per_week /
					frm.doc.working_time_per_weekday.length
			);
		}
	},
	prefill_working_days(frm) {
		frm.clear_table("working_time_per_weekday");
		const working_days = frm
			.get_docfield("working_time_per_weekday", "weekday")
			.options.split("\n")
			.slice(0, 5);
		for (const day of working_days) {
			frm.add_child("working_time_per_weekday", { weekday: day });
		}
		frm.refresh_field("working_time_per_weekday");
	}
});
