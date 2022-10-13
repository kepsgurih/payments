# Copyright (c) 2015, Frappe Technologies and contributors
# License: MIT. See LICENSE

"""
# Integrating PayPal

### 1. Validate Currency Support

Example:

	from payments.utils import get_payment_gateway_controller

	controller = get_payment_gateway_controller("PayPal")
	controller().validate_transaction_currency(currency)

### 2. Redirect for payment

Example:

	payment_details = {
		"amount": 600,
		"title": "Payment for bill : 111",
		"description": "payment via cart",
		"reference_doctype": "Payment Request",
		"reference_docname": "PR0001",
		"payer_email": "NuranVerkleij@example.com",
		"payer_name": "Nuran Verkleij",
		"order_id": "111",
		"currency": "USD",
		"payment_gateway": "Razorpay",
		"subscription_details": {
			"plan_id": "plan_12313", # if Required
			"start_date": "2018-08-30",
			"billing_period": "Month" #(Day, Week, SemiMonth, Month, Year),
			"billing_frequency": 1,
			"customer_notify": 1,
			"upfront_amount": 1000
		}
	}

	# redirect the user to this url
	url = controller().get_payment_url(**payment_details)


### 3. On Completion of Payment

Write a method for `on_payment_authorized` in the reference doctype

Example:

	def on_payment_authorized(payment_status):
		# your code to handle callback

##### Note:

payment_status - payment gateway will put payment status on callback.
For xendit payment status parameter is one from: [Completed, Cancelled, Failed]


More Details:
<div class="small">For details on how to get your API credentials, follow this link: <a href="https://developer.xendit.com/docs/classic/api/apiCredentials/" target="_blank">https://developer.xendit.com/docs/classic/api/apiCredentials/</a></div>

"""

import json
from urllib.parse import urlencode

import frappe
import pytz
from frappe import _, redirect
from frappe.integrations.utils import create_request_log, make_post_request
from frappe.model.document import Document
from frappe.utils import call_hook_method, cint, get_datetime, get_url
import requests
import midtransclient
from payments.utils import create_payment_gateway
from payments.utils import get_payment_gateway_controller


api_path = (
	"/api/method/payments.payment_gateways.doctype.midtrans_settings.midtrans_settings"
)


class MidtransSettings(Document):
	supported_currencies = [
		"IDR",
	]
	def validate_transaction_currency(self, currency):
		if currency not in self.supported_currencies:
			frappe.throw(
				_(
					"Please select another payment method. Stripe does not support transactions in currency '{0}'"
				).format(currency)
			)
	def validate(self):
		if not self.flags.ignore_mandatory:
			self.configure_midtrans()
	# controller = get_payment_gateway_controller("PayPal")
	# controller().validate_transaction_currency(currency)
	def get_payment_url(self, **kwargs):
		if self.midtrans_sandbox:
			is_production = False
		else:
			is_production = True
		param = {
			"transaction_details": {
				"order_id": kwargs.get("order_id"),
				"gross_amount": kwargs.get("amount")
				}, 
			"credit_card":{
				"secure" : True
			}
		}
		snap = midtransclient.Snap(
			is_production=is_production,
			server_key=self.server_key,
			client_key=self.client_key
		)
		transaction = snap.create_transaction(param)
		gets = {
			"pay":transaction['token'],
			"client":self.client_key
		}
		return get_url(f"./payment_checkout?{urlencode(gets)}")
	# 	# snap.create_transaction(param)
	# 	return redirect(self)
	def get_gateway_controller(doc):
		payment_request = frappe.get_doc("Payment Request", doc)
		gateway_controller = frappe.db.get_value(
			"Payment Gateway", payment_request.payment_gateway, "gateway_controller"
		)
		return gateway_controller