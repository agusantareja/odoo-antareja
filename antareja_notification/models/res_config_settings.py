# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    notification_email_test = fields.Char(
        string="Email Test",
        config_parameter='send_message_cron.test_email',
        default="False",
        help="""Set dengan alamat email tujuan untuk testing, Set dengan False bila tanpa"""
    )
    notification_wa_test = fields.Char(
        string="Test Mode",
        config_parameter='notif_wa_test',
        default="False"
    )
    notification_wa_scope = fields.Char(
        string="Scope Default",
        config_parameter='antareja_notification.scope_default',
        default="False"
    )
    module_antareja_notification_whatsapp = fields.Boolean("Notification Whatsapp")
    module_antareja_whatsapp_migration = fields.Boolean("WhatsApp Migration")
    module_auth_admin_sso = fields.Boolean()
    module_antareja_notification_admin_user = fields.Boolean("Ignore Admin User on Notification")
    module_antareja_notification_email_test = fields.Boolean("Email Test Forwarding")
