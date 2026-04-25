# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mobile_notification_server_auth_id = fields.Many2one(
        'application.server.auth',
        string='Notification Mobile Server Auth',
        config_parameter='antareja_notification_ceria_mobile_intra.mobile_notification_server_auth_id'
    )
    mobile_notification_endpoint = fields.Char(
        config_parameter='antareja_notification.mobile_notification_endpoint'
    )
    mobile_notification_token = fields.Char(
        config_parameter='antareja_notification.mobile_notification_token'
    )
    module_antareja_notification_ceria_mobile_local = fields.Boolean("Local Ceria Mobile Notification")
