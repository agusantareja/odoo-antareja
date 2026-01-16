# -*- coding: utf-8 -*-

import requests
import datetime
import jwt
import time
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import traceback
import logging

_logger = logging.getLogger(__name__)


class ApplicationServerAuth(models.Model):
    _inherit = 'application.server.auth'

    auth_type = fields.Selection(selection_add=[
        ('jwt-odoo-rcp', 'JWT Odoo RCP'),
        ('odoo-rcp',),
    ])

    rest_refresh = fields.Char()

    @api.model
    def rest_login_path(self):
        return '/api/application/login'

    @api.model
    def rest_profile_path(self):
        return '/api/application/profile'

    @api.model
    def rest_refresh_path(self):
        return '/api/application/refresh'

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

    def rest_login(self, login, password):
        rec = self.ensure_one()
        url = rec.rest_url(rec.rest_login_path())
        response = requests.post(url, data={'login': login, 'password': password})
        response.raise_for_status()
        json_result = response.json()
        rest_token = json_result.get('access_token')
        rest_refresh = json_result.get('refresh_token')
        if rest_token:
            rec.rest_token = rest_token
        if rest_refresh:
            rec.rest_refresh_token = rest_refresh
        return rest_token

    def rest_post_refresh(self, refresh_token=None):
        rec = self.ensure_one()
        refresh_token = refresh_token or rec.rest_refresh
        url = rec.rest_url(rec.rest_login_path())
        response = requests.post(url, data={'refresh_token': refresh_token})
        response.raise_for_status()
        json_result = response.json()
        rest_token = json_result.get('access_token')
        rest_refresh = json_result.get('refresh_token')
        if rest_token:
            rec.rest_token = rest_token
        if rest_refresh:
            rec.rest_token_refresh = rest_refresh
        return rest_token

    def ensure_token(self):
        rec = self.ensure_one()
        if rec.auth_type in ['jwt-odoo-rcp', 'jwt-rest-token'] and rec.is_token_expired():
            rec.rest_post_refresh()
        return rec.rest_token

    def jsonrpc_authenticate(self):
        rec = self.ensure_one()
        db, uid, token = None, None, rec.ensure_token()
        if rec.auth_type == 'jwt-odoo-rcp':
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
            db, uid, token = super(ApplicationServerAuth, self).jsonrpc_authenticate()
        return db, uid, token

    def action_login(self):
        for rec in self:
            username, password = rec.get_odoo_username_password()
            rec.rest_login(username, rec.password)
        return True
