# -*- coding: utf-8 -*-

import requests
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import traceback
import logging

_logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return fields.Datetime.to_string(obj)

        if isinstance(obj, datetime.date):
            return fields.Date.to_string(obj)

        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8")
        return json.JSONEncoder.default(self, obj)

class ApplicationServerAuthOdooRCP(models.AbstractModel):
    _name = 'application.server.auth.odoo.rcp.mixin'

    # odoo rcp
    odoo_server_db = fields.Char()
    odoo_server_uid = fields.Integer(readonly=True)
    odoo_username = fields.Char()
    odoo_password = fields.Char()


class ApplicationServerAuthRestToken(models.AbstractModel):
    _name = 'application.server.auth.rest.token.mixin'

    # rest-token
    rest_token_in = fields.Selection([(
        'header', 'Header'), ('param', 'Parameter'), ('body', 'Body')
    ], default='header')
    rest_token_key = fields.Char(
        default='access_token'
    )
    rest_token = fields.Char()

    def rest_endpoint_url(self):
        raise NotImplemented

    def rest_url(self,path):
        return f"{self.rest_endpoint_url()}{path}"

    def rest_headers(self,headers):

        return headers


    def rest_params(self, params):
        return params

    def rest_get(self,path="",params=None,headers=None, **kwargs):
        rec = self.ensure_one()
        url = rec.rest_url(path)
        headers = rec.rest_headers(headers)
        params = rec.rest_params(params)
        return requests.get(url, params=params,headers=headers,**kwargs)


    def rest_post(self,path="",params=None, headers=None, **kwargs):
        rec = self.ensure_one()
        url = rec.rest_url(path)
        headers = rec.rest_headers(headers)
        params = rec.rest_params(params)

        return requests.post(url, params=params, headers=headers, **kwargs)


class ApplicationServerAuth(models.Model):
    _name = 'application.server.auth'
    _inherit = ['application.server.auth.odoo.rcp.mixin','application.server.auth.rest.token.mixin']

    active = fields.Boolean(default=True)
    name = fields.Char()
    application_server_id = fields.Many2one('application.server')

    auth_type = fields.Selection([
        ('odoo-rcp', 'Odoo RCP'),
        ('rest-token', 'Rest Token'),
    ], default='rest-token')

    config_param_param = fields.Char()

    def rest_endpoint_url(self):
        return self.application_server_id.endpoint