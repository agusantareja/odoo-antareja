# -*- coding: utf-8 -*-

from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mobile_notification_send_method = fields.Selection(
        [('local', 'Local'), ('intra', 'Intra'),],default='intra',
        config_parameter = 'antareja_notification.mobile_notification_send_method',
    )

