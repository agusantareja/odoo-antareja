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
