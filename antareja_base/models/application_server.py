# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError
from odoo.models import BaseModel
from ..tools.utils import have_method
import logging

_logger = logging.getLogger(__name__)


class ApplicationServer(models.Model):
    _name = 'application.server'
    _inherit = 'ir.config_parameter.able.mixin'
    _description = 'Application Server Integration for multi Application Server'

    name = fields.Char('Name')
    description = fields.Char()
    endpoint = fields.Char(compute='compute_endpoint')
    endpoint_value = fields.Char()
    application_server_auth_ids = fields.One2many(
        'application.server.auth','application_server_id',
        readonly=True
    )
    application_server_path_ids = fields.One2many(
        'application.server.path', 'application_server_id',
        readonly = True
    )

    @api.depends('endpoint_value','config_param_name')
    def compute_endpoint(self):
        for rec in self:
            rec.endpoint=rec.get_value_config_param(value_without_config_param=self.endpoint_value)