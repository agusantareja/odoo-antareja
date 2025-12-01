# -*- coding: utf-8 -*-
import json

from odoo import models

import logging
_logger = logging.getLogger(__name__)



class NotificationMobileTemplate(models.Model):
    _inherit = "notification.mobile.template"

    def get_mobile_notification_client(self):
        return self.env['mobile.notification.client']

    def send_notification(self,payload):
        mobile_notification_client = self.get_mobile_notification_client()
        notif= mobile_notification_client.create_payload(**payload)
        notif.process()
        return notif
