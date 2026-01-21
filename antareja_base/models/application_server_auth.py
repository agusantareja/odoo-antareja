# -*- coding: utf-8 -*-

from requests import RequestException
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import requests
import logging

_logger = logging.getLogger(__name__)


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
    rest_refresh = fields.Char()

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

    @api.model
    def rest_headers(self, headers=None):
        return headers

    def rest_params(self, params):
        return params

    def get_rest_token(self):
        return self.rest_token

    def ensure_token(self):
        return self.get_rest_token()

    def rest_profile(self):
        raise NotImplemented

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

    def get_odoo_server_uid(self):
        return self.odoo_server_uid

    def get_db_uid_username_password(self):
        raise NotImplemented

    def get_odoo_username_password(self):
        raise NotImplemented

    @api.model
    def get_jsonrpc_db_name(self):
        return '/sync/db_name'

    @api.model
    def get_jsonrpc_path(self):
        return '/jsonrpc'

    @api.model
    def get_jsonrpc_url(self):
        return self.rest_url(self.get_jsonrpc_path())

    def action_get_odoo_db_name(self):
        url = self.rest_url(self.get_jsonrpc_db_name())
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            db = result.get('db')
            if not db:
                raise UserError('DB not found')
            self.odoo_server_db=db
        except RequestException as e:
            raise UserError(str(e))

    def action_get_odoo_server_uid(self):
        try:
            db, uid, password = self.jsonrpc_authenticate()
            if uid:
                self.write({'odoo_server_uid': uid})
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Info',
                        'message': _("Get UID successful. (DB: %s, UID: %s)") % (db, uid),
                        'type': 'info',
                    }
                }
            else:
                raise UserError(_("Authentication failed. Please check your credentials."))
        except Exception as e:
            raise UserError(_("Connection failed: %s") % str(e))

    def action_test_connection(self):
        try:
            db, uid, password = self.jsonrpc_authenticate()
            if not uid:
                raise UserError(_("Authentication failed. Please check your credentials."))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Info',
                    'message': _("Connection successful. (DB: %s, UID: %s)") % (db, uid),
                    'type': 'info',
                }
            }
        except Exception as e:
            raise UserError(_("Connection failed: %s") % str(e))

    def jsonrpc_post(self, obj_payload):
        raise NotImplemented

    def jsonrpc_authenticate(self):
        raise NotImplemented

    def jsonrpc_execute_kw(self, model, method, args, kw=None, db=None, uid=None, password=None):
        raise NotImplemented

    def jsonrpc_call(self, model, method, args, kw=None, db=None, uid=None, password=None):
        raise NotImplemented


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

    def get_odoo_db_username_password(self):
        db = self.get_odoo_server_db()
        username, password = self.get_odoo_username_password()
        return db, username, password

    def get_db_uid_username_password(self):
        db = self.get_odoo_server_db()
        uid = self.get_odoo_server_uid()
        username, password = self.get_odoo_username_password()
        return db, uid, username, password

    def get_rest_token(self):
        return self.get_value_config_param(value_without_config_param=self.rest_token)

    def rest_endpoint_url(self):
        self.ensure_one()
        endpoint_url = self.application_server_id.get_endpoint_url()
        _logger.info(f"Endpoint URL : {endpoint_url}")
        return self.application_server_id.get_endpoint_url()

    def action_open_view(self):
        self.ensure_one()
        context = dict(self.env.context, default_application_server_id=self.id)
        return {
            'name': _('Server Auth'),
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'context': context
        }
