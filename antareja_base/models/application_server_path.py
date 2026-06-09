# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ApplicationServerPath(models.Model):
    _name = 'application.server.path'
    # _inherit = 'ir.config_parameter.able.mixin'
    #
    # active = fields.Boolean(default=True)
    # name = fields.Char()
    # application_server_auth_id = fields.Many2one(
    #     'application.server.auth',
    #     domain=[('auth_type', '=', 'rest-token')]
    # )
    # application_server_id = fields.Many2one(
    #     'application.server',
    #     related='application_server_auth_id.application_server_id',
    #     store=True,
    #     readonly=True
    # )
    # path = fields.Char(compute='compute_path')
    # path_value = fields.Char()
    #
    # @api.depends('path_value', 'config_param_name')
    # def compute_path(self):
    #     for rec in self:
    #         if rec.config_param_name:
    #             rec.path = rec.get_value_config_param(config_param_name=rec.config_param_name)
    #         else:
    #             rec.path = rec.path_value
