import frappe


def get_context(context):
	if frappe.session.user == "Guest" or "System Manager" not in frappe.get_roles():
		frappe.throw("Not permitted.", frappe.PermissionError)
	context.no_cache = 1
