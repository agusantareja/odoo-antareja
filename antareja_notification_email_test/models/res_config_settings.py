from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    notification_email_test = fields.Char(
        string="Email Test",
        config_parameter='send_message_cron.test_email',
        default="False",
        help="""Set dengan alamat email tujuan untuk testing, Set dengan False bila tanpa"""
    )
