# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    antareja_token_expires_in = fields.Integer(
        "Expired in (sec)",
        config_parameter='antareja_token.expires_in',
    )
    antareja_token_retention_in = fields.Integer(
        "Retention in (sec)",
        config_parameter='antareja_token.retention_in',
    )

    antareja_token_secret = fields.Char(
        "Secret",
        config_parameter='antareja_token.secret',
    )
    module_antareja_token_oauth = fields.Boolean("Token OAuth")

    def create_jwt_token(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Token',
            'view_mode': 'form',
            'res_model': 'antareja.create.token.wizard',
            # 'res_id': self.env.company.id,
            'target': 'current',
            # 'context': {
            #     'form_view_initial_mode': 'edit',
            # },
        }
