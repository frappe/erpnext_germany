from erpnext_germany.install import import_csv
from frappe import get_app_path


def execute():
	import_csv("Business Trip Region", get_app_path("erpnext_germany", "data", "business_trip_region.csv"))
