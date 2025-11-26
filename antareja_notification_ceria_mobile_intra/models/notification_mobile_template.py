# -*- coding: utf-8 -*-
import json

from odoo import models

import logging
_logger = logging.getLogger(__name__)



class NotificationMobileTemplate(models.Model):
    _inherit = "notification.mobile.template"

    def send_notification(self,payload):
        config = self.env['ir.config_parameter'].sudo()
        method = config.get_param('antareja_notification.mobile_notification_token')
        if 'ceria.mobile.notification' in self.env and method=='local':
            mobile_notification_client = self.env['ceria.mobile.notification']
        else:
            mobile_notification_client =self.env['mobile.notification.client']
        notif= mobile_notification_client.create_payload(**payload)
        notif.process()
        return notif



