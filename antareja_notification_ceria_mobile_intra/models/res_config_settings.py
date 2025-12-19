# -*- coding: utf-8 -*-

from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    mobile_notification_endpoint = fields.Char(
        config_parameter='antareja_notification.mobile_notification_endpoint'
    )
    mobile_notification_token = fields.Char(
        config_parameter='antareja_notification.mobile_notification_token'
    )
    module_antareja_notification_ceria_mobile_local = fields.Boolean("Local Ceria Mobile Notification")
    module_antareja_notification_ceria_mobile_token = fields.Boolean("Notification Ceria Mobile Token")
