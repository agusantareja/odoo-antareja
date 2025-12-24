# -*- coding: utf-8 -*-

import requests
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import traceback
import logging
from datetime import datetime, timedelta

from ..tools.utils import save_call_method

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
    # 
    # def set_value_from_config_parameter(self,config_param_name,config_param_value):
    #     records=self.sudo().search([('config_param_name','=',config_param_name)])
    #     records.write({
    #         'config_param_value':config_param_value
    #     })

    def get_value_config_param(self, config_param_name=None,value_without_config_param=None):
        config_param_name = config_param_name or self and self.config_param_name
        if config_param_name:
            return self.env['ir.config_parameter'].sudo().get_param(config_param_name) or None
        else:
            return value_without_config_param

# class IrConfigParameter(models.Model):
#     _inherit = 'ir.config_parameter'
# 
#     # def create(self, vals_list):
#     #     return super(IrConfigParameterSync, self).create(vals_list)
# 
#     def sync_data(self):
#         for rec in self:
#             for model_name in self.env:
#                 model = self.env[model_name]
#                 if have_method(model,'set_value_from_config_parameter'):
#                     model.set_value_config(rec.key,rec.value)
#                 
# 
#     @api.model_create_multi
#     def create(self, vals_list):
#         records= super(IrConfigParameter, self).create(vals_list)
#         records.sync_data()
#         return records
# 
#     def write(self, vals):
# 
#         result= super(IrConfigParameter, self).write(vals)
#         self.sync_data()
#         return result