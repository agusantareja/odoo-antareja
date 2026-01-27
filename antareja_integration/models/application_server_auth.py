# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.amr_jsonrpc import jsonrpc, rest
import requests
import jwt
import time
import logging

_logger = logging.getLogger(__name__)


class ApplicationServerAuth(models.Model):
    _name = 'application.server.auth'
    _inherit = [_name, 'client.auth.mixin']
    auth_type = fields.Selection(selection_add=[
        ('jwt-odoo-rcp', 'JWT Odoo RCP'),
        ('jwt-rest-token', 'JWT rest-token'),
    ])

    rest_refresh = fields.Char()
    access_token = fields.Char(related="rest_token", store=True)
    refresh_token = fields.Char(related="rest_refresh", store=True)

    def get_db_name(self):
        return self.odoo_server_db

    @api.model
    def rest_login_path(self):
        return '/application/token'

    @api.model
    def rest_profile_path(self):
        return '/application/profile'

    @api.model
    def rest_refresh_path(self):
        return '/application/token'

    def get_token_endpoint_url(self):
        return self.rest_url(self.rest_login_path())

    def get_endpoint_url(self):
        return self.application_server_id.get_endpoint_url()

    def is_jwt(self):
        try:
            jwt.get_unverified_header(self.rest_token)
            return True
        except jwt.InvalidTokenError:
            return False

    def is_token_expired(self):
        payload = jwt.decode(
            self.rest_token,
            options={"verify_signature": False}
        )
        exp = payload.get("exp")
        if not exp:
            return True  # tidak ada exp → anggap expired

        now = int(time.time())
        return now >= exp

    # def rest_login(self, login, password, **kwargs):
    #     rec = self.ensure_one()
    #     url = rec.rest_url(rec.rest_login_path())
    #     rest_token, rest_refresh = rest.request_token(url, login, password, **kwargs)
    #     rec.rest_token = rest_token or rec.rest_token
    #     rec.rest_refresh_token = rest_refresh or rec.rest_refresh_token
    #     return rest_token

    # def rest_headers(self, headers=None):
    #     if self.rest_token_in == 'basic':
    #         return self.rest_basic_header(headers)
    #     if self.rest_token_in == 'bearer':
    #         return self.rest_bearer_header(headers)
    #     if self.rest_token_in == 'header':
    #         if headers is None:
    #             headers = {}
    #         headers[self.rest_token_key] = self.get_rest_token()
    #     return headers

    # def rest_basic_header(self, headers=None):
    #     username, password = self.get_username_password()
    #     return rest.basic_auth_header(username, password, headers)

    def rest_bearer_header(self, headers=None):
        return rest.bearer_auth_header(self.ensure_token(), headers)

    # def rest_profile(self):
    #     rec = self.ensure_one()
    #     url = rec.rest_url(rec.rest_profile_path())
    #     response = requests.get(url, rec.rest_bearer_header())
    #     response.raise_for_status()
    #     return response.json()

    def rest_post_refresh(self, refresh_token=None, **kwargs):
        rec = self.ensure_one()
        refresh_token = refresh_token or rec.rest_refresh
        url = rec.rest_url(rec.rest_login_path())
        rest_token, rest_refresh = rest.request_refresh_token(url, refresh_token)
        rec.rest_token = rest_token or rec.rest_token
        rec.rest_token_refresh = rest_refresh or rec.rest_token_refresh
        return rest_token

    def ensure_token(self):
        rec = self.ensure_one()
        if rec.auth_type in ['jwt-odoo-rcp', 'jwt-rest-token'] and rec.is_token_expired():
            rec.rest_post_refresh()
        return rec.rest_token

    def jsonrpc_authenticate(self):
        rec = self.ensure_one()
        if rec.auth_type == 'jwt-odoo-rcp':
            db, uid, token = None, None, rec.ensure_token()
            if rec.is_jwt():
                payload = jwt.decode(token, options={"verify_signature": False})
                db = payload.get("db", None)
                uid = payload.get("uid", None)
            else:
                headers = {'Authorization': f'Bearer {token}'}
                url = rec.rest_url(rec.rest_profile_path())
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                json_result = response.json()
                db = json_result.get('db')
                uid = json_result.get('uid')
            if not db or not uid:
                raise UserError(_("Invalid JWT Token"))
        else:
            db, username, password = self.get_odoo_db_username_password()
            db, uid, token = jsonrpc.authenticate(self.get_jsonrpc_url(), db, username, password)
        return db, uid, token

    def jsonrpc_execute_kw(self, model, method, args, kw=None, db=None, uid=None, password=None):
        """Deprecated gunakan remote_model_object"""
        return jsonrpc.execute_kw(self.get_jsonrpc_url(), model, method, args, kw=kw, db=db, uid=uid, password=password)

    def jsonrpc_call(self, model, method, args, kw=None, db=None, uid=None, password=None):
        """Deprecated gunakan remote_model_object"""
        if not db or not uid or not password:
            db, uid, password = self.jsonrpc_authenticate()
        return jsonrpc.execute_kw(self.get_jsonrpc_url(), model, method, args, kw=kw, db=db, uid=uid, password=password)

    # def action_login(self):
    #     self.ensure_one()
    #     try:
    #         username, password = self.get_odoo_username_password()
    #         self.rest_login(username, password)
    #         return {
    #             'type': 'ir.actions.client',
    #             'tag': 'display_notification',
    #             'params': {
    #                 'title': 'Info',
    #                 'message': _("Token successful."),
    #                 'type': 'info',
    #             }
    #         }
    #     except Exception as e:
    #         raise UserError(_("Get Token failed: %s") % str(e))

    # def get_auth_config(self, config=None):
    #     config = {}
    #     auth_type = self.auth_type
    #     token_key = self.rest_token_key
    #     access_token = self.rest_token
    #     refresh_token = self.rest_refresh
    #     token_endpoint_url = self.rest_url(self.rest_login_path())
    #     if self.auth_type in ['jwt-rest-token', 'rest-token']:
    #         auth_type = self.rest_token_in
    #     if self.auth_type in ['rest-token', 'rest-token']:
    #         endpoint_url = self.rest_endpoint_url()
    #     else:
    #         endpoint_url = self.get_jsonrpc_url()
    #     db, uid, username, password = self.get_db_uid_username_password()
    #     config.update({
    #         'db': db,
    #         'uid': uid,
    #         'username': username,
    #         'password': password,
    #         'auth_mode': auth_type,
    #         'token_key': token_key,
    #         'access_token': access_token,
    #         'refresh_token': refresh_token,
    #         'endpoint_url': endpoint_url,
    #         'token_endpoint_url': token_endpoint_url
    #     })
    #     return config
    #
    # def remote_model_object(self, external_model, **kwargs):
    #     config = self.get_auth_config()
    #     config.update(kwargs)
    #     if self.auth_type in ['jwt-rest-token', 'rest-token']:
    #         return rest.model_object(external_model, **config)
    #     else:
    #         return jsonrpc.model_object(external_model, **config)
