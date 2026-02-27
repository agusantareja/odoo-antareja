# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    notification_wa_scope = fields.Char(
        string="Scope Default",
        config_parameter='antareja_notification.scope_default',
        default="False",
    )
