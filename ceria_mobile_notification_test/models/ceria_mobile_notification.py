# -*- coding: utf-8 -*-

from odoo import api, fields, models
from firebase_admin import messaging

import json
import traceback


class CeriaMobileNotification(models.Model):
    _inherit = "ceria.mobile.notification"

    @api.model
    def get_device_test_token(self):
        return self.env['ir.config_parameter'].get_param('ceria_mobile_notification.device_test_token')

    def get_devices_token(self):
        device_test_token = self.get_device_test_token()
        if device_test_token:
            return [self.get_device_test_token()]
        else:
            raise ValueError("Device Test Token not setup properly")
