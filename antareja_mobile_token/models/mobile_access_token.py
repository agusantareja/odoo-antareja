# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from datetime import datetime, timedelta

from odoo.exceptions import AccessDenied
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

try:
    from oauthlib import common as oauthlib_common
except ImportError:
    _logger.warning(
        'OAuth library not found. If you plan to use it, '
        'please install the oauth library from '
        'https://pypi.python.org/pypi/oauthlib')

class MobileAccessToken(models.Model):
    _name = 'mobile.access.token'
    active = fields.Boolean(default=True)
    token = fields.Char('Access Token', required=True)
    user_id = fields.Many2one('res.users', string='User')
    expires = fields.Datetime('Expires')

    def token_expires_in(self):
        return int(self.env['ir.config_parameter'].sudo().get_param('antareja_mobile_token.expires_in')) or (
                60 * 60 * 24)

    def generate_token(self,user_id):
        vals = {
            'user_id': user_id,
            'token': oauthlib_common.generate_token(),
        }
        expires_in = self.token_expires_in()
        expires = datetime.now() + timedelta(seconds=expires_in)
        vals['expires'] = expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return vals

    def get_jwt_secret(self):
        return self.env['ir.config_parameter'].sudo().get_param('jwt.secret')

    def get_jwt_algorithm(self):
        return 'HS256'

    def generate_jwt_token(self,uid,login):
        jwt_secret = self.get_jwt_secret()
        if not jwt_secret:
            return None
        expires_in = self.token_expires_in()
        try:
            import jwt
            payload = {
                'uid': uid,
                'login': login,
                'exp': datetime.utcnow() + timedelta(seconds=expires_in)
            }
            return jwt.encode(payload, self.get_jwt_secret(), algorithm=self.get_jwt_algorithm())
        except ImportError:
            return None


    def validate_jwt(self,token):
        try:
            import jwt
            from jwt import ExpiredSignatureError, InvalidTokenError
            try:
                payload = jwt.decode(
                    token,
                    self.get_jwt_secret(),
                    algorithms=[self.get_jwt_algorithm()]
                )
                return payload
            except ExpiredSignatureError:
                return None
            except InvalidTokenError:
                return None
        except ImportError:
            return None


    def validate(self,token):
        jwt_data = self.validate_jwt(token)
        if jwt_data:
            return jwt_data
        res = self.sudo().search([('token', '=', token)], order='id DESC', limit=1)
        if res.is_expired():
            return None
        return {
            'uid': res.user_id.id,
            'login': res.user_id.login,
        }

    def _get_access_token(self, user_id=None, create=False,login=None):
        if not user_id:
            user_id = self.env.user.id
        if not login:
            login = self.user_id.sudo().browse(user_id).login

        access_token = self.sudo().search(
            [('user_id', '=', user_id)], order='id DESC', limit=1)
        if access_token:
            access_token = access_token[0]
            if access_token.is_expired():
                access_token = None
        if not access_token and create:
            vals = self.generate_jwt_token(user_id,login) or self.generate_token(user_id)
            access_token = self.sudo().create(vals)
            # we have to commit now
            # be called before we finish current transaction.
            self._cr.commit()
        if not access_token:
            return None
        return access_token.token

    def is_expired(self):
        self.ensure_one()
        if not self.expires:
            return False
        return datetime.now() > fields.Datetime.from_string(self.expires)

    def get_user(self,mobile_token):
        return self.sudo().search([('token', '=', mobile_token)], order='id DESC', limit=1).user_id
