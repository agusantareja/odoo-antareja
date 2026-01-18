# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.amr_jsonrpc import jsonrpc, rest
import requests
import datetime
import jwt
import time

import base64
import json
import traceback
import logging

_logger = logging.getLogger(__name__)


class ApplicationServerAuth(models.Model):
    _inherit = 'application.server.auth'

    auth_type = fields.Selection(selection_add=[
        ('jwt-odoo-rcp', 'JWT Odoo RCP'),
        ('jwt-rest-token', 'JWT rest-token'),
    ])

    rest_refresh = fields.Char()

    @api.model
    def rest_login_path(self):
        return '/application/token'

    @api.model
    def rest_profile_path(self):
        return '/application/profile'

    @api.model
    def rest_refresh_path(self):
        return '/application/token'

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

    def rest_login(self, login, password, **kwargs):
        rec = self.ensure_one()
        url = rec.rest_url(rec.rest_login_path())
        rest_token, rest_refresh = rest.request_token(url, login, password, **kwargs)
        rec.rest_token = rest_token or rec.rest_token
        rec.rest_refresh_token = rest_refresh or rec.rest_refresh_token
        return rest_token

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
        username, password = self.get_username_password()
        return rest.basic_auth_header(username, password, headers)

    def rest_bearer_header(self, headers=None):
        return rest.bearer_auth_header(self.ensure_token(), headers)

    def rest_profile(self):
        rec = self.ensure_one()
        url = rec.rest_url(rec.rest_profile_path())
        response = requests.get(url, rec.rest_bearer_header())
        response.raise_for_status()
        return response.json()

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
        return jsonrpc.execute_kw(self.get_jsonrpc_url(), model, method, args, kw=kw, db=db, uid=uid, password=password)

    def jsonrpc_call(self, model, method, args, kw=None, db=None, uid=None, password=None):
        if not db or not uid or not password:
            db, uid, password = self.jsonrpc_authenticate()
        return jsonrpc.execute_kw(self.get_jsonrpc_url(), model, method, args, kw=kw, db=db, uid=uid, password=password)

    def action_login(self):
        self.ensure_one()
        try:
            username, password = self.get_odoo_username_password()
            self.rest_login(username, password)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Info',
                    'message': _("Token successful."),
                    'type': 'info',
                }
            }
        except Exception as e:
            raise UserError(_("Get Token failed: %s") % str(e))
