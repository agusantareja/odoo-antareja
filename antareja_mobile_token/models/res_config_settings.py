# -*- coding: utf-8 -*-

from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    antareja_mobile_token_expires_in = fields.Integer(
        "Expired in (sec)",
        config_parameter='antareja_mobile_token.expires_in',
    )
