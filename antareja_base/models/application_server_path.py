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

    active = fields.Boolean(default=True)
    name = fields.Char()
    # application_server_id = fields.Many2one('application.server')
    application_server_auth_id = fields.Many2one('application.server.auth')
    path = fields.Char()
    config_param_param = fields.Char()

    def rest_get(self,params=None,headers=None, **kwargs):
        rec = self.ensure_one()
        return rec.application_server_auth_id.rest_get(rec.path, params=params,headers=headers,**kwargs)

    def rest_post(self,params=None, headers=None, **kwargs):
        rec = self.ensure_one()
        return rec.application_server_auth_id.rest_post(rec.path, params=params, headers=headers, **kwargs)
