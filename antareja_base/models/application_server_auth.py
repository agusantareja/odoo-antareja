# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import requests
import base64
import logging

_logger = logging.getLogger(__name__)

class RemoteModelObject(object):

    def __init__(
        self,
        auth,
        model_name,
        context = None
    ):
        self.auth = auth
        self.model_name = model_name
        self.context = context

    def __getattr__(self, method):
        def delay(*args, **kw):
            return self.auth.jsonrpc_call(self.model_name,method,args=args,kw=kw)
        return delay

    def __str__(self):
        return "RemoteModelObject({})".format(self.model_name)

    __repr__ = __str__

class ApplicationServerAuthRestToken(models.AbstractModel):
    _name = 'application.server.auth.rest.token.mixin'

    # rest-token
    rest_token_in = fields.Selection([
        ('basic', 'Basic'),
        ('bearer', 'Bearer'),
        ('header', 'Header'),
        ('param', 'Parameter'),
        ('body', 'Body')
    ], default='header')
    rest_token_key = fields.Char(
        default='basic'
    )
    rest_token = fields.Char()

    def rest_endpoint_url(self):
        raise NotImplemented

    def rest_url(self, path):
        rest_endpoint = self.rest_endpoint_url()
        if not path or path == '/':
            return rest_endpoint
        if path.startswith('http'):
            return path
        if not path.startswith('/'):
            path = f'/{path}'
        return f"{rest_endpoint}{path}"

    def rest_headers(self, headers=None):
        if self.rest_token_in == 'basic':
            return self.rest_basic_header(headers)
        if self.rest_token_in == 'bearer':
            return self.rest_bearer_header(headers)
        if self.rest_token_in == 'header':
            if headers is None:
                headers = {}
            headers[self.rest_token_key] = self.get_rest_token()
        return headers

    def rest_basic_header(self, headers=None):
        if headers is None:
            headers = {}
        username, password = self.get_username_password()
        token = f"{username}:{password}"
        encoded = base64.b64encode(token.encode()).decode()
        headers['Authorization'] = f"Basic {encoded}"
        return headers

    def rest_bearer_header(self, headers=None):
        if headers is None:
            headers = {}
        headers['Authorization'] = f'Bearer {self.ensure_token()}'
        return headers

    def rest_params(self, params):
        return params

    def get_rest_token(self):
        return self.rest_token

    def ensure_token(self):
        return self.get_rest_token()

    def rest_profile(self):
        rec = self.ensure_one()
        url = rec.rest_url(rec.rest_profile_path())
        response = requests.get(url, rec.rest_bearer_header())
        response.raise_for_status()
        return response.json()

    def rest_get(self, path="", params=None, headers=None, **kwargs):
        rec = self.ensure_one()
        url = rec.rest_url(path)
        headers = rec.rest_headers(headers)
        params = rec.rest_params(params)
        return requests.get(url, params=params, headers=headers, **kwargs)

    def rest_post(self, path="", params=None, headers=None, **kwargs):
        rec = self.ensure_one()
        url = rec.rest_url(path)
        headers = rec.rest_headers(headers)
        params = rec.rest_params(params)

        return requests.post(url, params=params, headers=headers, **kwargs)


class ApplicationServerAuthOdooRCP(models.AbstractModel):
    _name = 'application.server.auth.odoo.rcp.mixin'
    _inherit = 'application.server.auth.rest.token.mixin'
    # odoo rcp
    odoo_server_db = fields.Char()
    odoo_server_uid = fields.Integer()
    odoo_username = fields.Char()
    odoo_password = fields.Char()

    def get_odoo_server_db(self):
        return self.odoo_server_db

    def get_odoo_username_password(self):
        raise NotImplemented

    @api.model
    def get_jsonrpc_path(self):
        return '/jsonrpc'

    @api.model
    def get_jsonrpc_url(self):
        return self.rest_url(self.get_jsonrpc_path())

    def jsonrpc_post(self, obj_payload):
        response = requests.post(self.get_jsonrpc_url(), json=obj_payload)
        response.raise_for_status()
        return response.json()

    def jsonrpc_authenticate(self):
        db = self.odoo_server_db
        uid = self.odoo_server_uid
        username, password = self.get_odoo_username_password()
        if not uid:
            # 1. Authenticate
            auth_payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [db, username, password, {}]
                },
                "id": 1,
            }
            # res = self.jsonrpc_post(auth_payload)
            # url = self.rest_url(self.get_jsonrpc_path())
            # response = requests.post(url, json=auth_payload)
            # response.raise_for_status()
            res = self.jsonrpc_post(auth_payload)
            uid = res.get("result")
        return db, uid, password

    def jsonrpc_call(self, model, method, args, kw=None, db=None, uid=None, password=None):
        if not db or not uid or not password:
            db, uid, password = self.jsonrpc_authenticate()
        args = [
            db,
            uid,
            password,
            model,
            method,
            args,
            kw
        ]
        obj_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": args,
            },
            "id": 2,
        }
        try:
            json_data = self.jsonrpc_post(obj_payload)
            # url = self.rest_url(self.get_jsonrpc_path())
            # response = requests.post(url, json=obj_payload)
            # response.raise_for_status()
            # json_data = response.json()
            if "error" in json_data:
                raise Exception(f"Odoo Error: {json_data['error']}")
            return json_data.get("result")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network Error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected Error: {str(e)}")

    @api.model
    def get_remote_model(self, model,context=None):
        return RemoteModelObject( model, context)


class ApplicationServerAuth(models.Model):
    _name = 'application.server.auth'
    _inherit = ['application.server.auth.odoo.rcp.mixin',
                'ir.config_parameter.able.mixin']

    active = fields.Boolean(default=True)
    name = fields.Char()
    application_server_id = fields.Many2one(
        'application.server'
    )
    application_server_path_ids = fields.One2many(
        'application.server.path',
        'application_server_auth_id'
    )
    auth_type = fields.Selection([
        ('odoo-rcp', 'Odoo RCP'),
        ('rest-token', 'Rest Token'),
    ], default='rest-token')

    username = fields.Char()
    password = fields.Char()

    def get_username_password(self):
        return self.username, self.password

    def get_odoo_username_password(self):
        return self.username, self.password

    def get_rest_token(self):
        return self.get_value_config_param(value_without_config_param=self.rest_token)

    def rest_endpoint_url(self):
        self.ensure_one()
        endpoint_url = self.application_server_id.get_endpoint_url()
        _logger.info(f"Endpoint URL : {endpoint_url}")
        return self.application_server_id.get_endpoint_url()
