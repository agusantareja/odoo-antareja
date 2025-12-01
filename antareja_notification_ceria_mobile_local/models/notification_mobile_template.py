# -*- coding: utf-8 -*-
import json

from odoo import models

import logging
_logger = logging.getLogger(__name__)



class NotificationMobileTemplate(models.Model):
    _inherit = "notification.mobile.template"

    def get_mobile_notification_client(self):
        return self.env['ceria.mobile.notification']
