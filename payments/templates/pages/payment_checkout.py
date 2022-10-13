import frappe

expected_keys = (
	"pay"
)
def get_context(context):
    context['pay'] = frappe.form_dict['pay']
    context['client'] = frappe.form_dict['client']