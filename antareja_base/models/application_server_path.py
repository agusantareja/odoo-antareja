# -*- coding: utf-8 -*-

import requests
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import traceback
import logging

_logger = logging.getLogger(__name__)



class ApplicationServerPath(models.Model):
    _name = 'application.server.path'
    _inherit = 'ir.config_parameter.able.mixin'

    active = fields.Boolean(default=True)
    name = fields.Char()
    application_server_auth_id = fields.Many2one('application.server.auth')
    application_server_id = fields.Many2one(
        'application.server',
        related='application_server_auth_id.application_server_id',
        store=True,
        readonly=True
    )
    path = fields.Char()

    def get_path(self):
        return self.get_value_config_param( value_without_config_param=self.path)

    def rest_get(self,params=None,headers=None, **kwargs):
        rec = self.ensure_one()
        return rec.application_server_auth_id.rest_get(rec.path, params=params,headers=headers,**kwargs)

    def rest_post(self,params=None, headers=None, **kwargs):
        rec = self.ensure_one()
        return rec.application_server_auth_id.rest_post(rec.path, params=params, headers=headers, **kwargs)
