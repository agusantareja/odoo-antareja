# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ApplicationServer(models.Model):
    _name = 'application.server'
    _inherit = 'ir.config_parameter.able.mixin'
    _description = 'Application Server Integration for multi Application Server'

    active = fields.Boolean(default=True)
    name = fields.Char('Name')
    description = fields.Char()
    endpoint = fields.Char(compute='compute_endpoint')
    endpoint_value = fields.Char()

    @api.depends('endpoint_value', 'config_param_name')
    def compute_endpoint(self):
        for rec in self:
            if rec.config_param_name:
                rec.endpoint = rec.get_value_config_param(config_param_name=rec.config_param_name)
            else:
                rec.endpoint = rec.endpoint_value

    def get_endpoint_url(self):
        return self.endpoint
