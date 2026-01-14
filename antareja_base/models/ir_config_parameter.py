# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import logging

_logger = logging.getLogger(__name__)


class IrConfigParameterSync(models.AbstractModel):
    _name = "ir.config_parameter.able.mixin"

    config_param_name = fields.Char()

    def open_config_parameter(self):
        param = self.env['ir.config_parameter'].sudo().search(
            [('key', '=', self.config_param_name)],
            limit=1
        ) or self.env['ir.config_parameter'].sudo().create({'key': self.config_param_name, 'value': ""})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.config_parameter',
            'res_id': param.id,
            'view_mode': 'form',
        }

    def get_value_config_param(self, config_param_name=None, value_without_config_param=None):
        config_param_name = config_param_name or self and self.config_param_name
        if config_param_name:
            return self.env['ir.config_parameter'].sudo().get_param(config_param_name) or None
        else:
            return value_without_config_param
