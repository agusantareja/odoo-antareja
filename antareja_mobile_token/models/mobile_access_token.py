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

    def _get_access_token(self, user_id=None, create=False):
        if not user_id:
            user_id = self.env.user.id

        access_token = self.sudo().search(
            [('user_id', '=', user_id)], order='id DESC', limit=1)
        if access_token:
            access_token = access_token[0]
            if access_token.is_expired():
                access_token = None
        if not access_token and create:
            vals = {
                'user_id': user_id,
                'token': oauthlib_common.generate_token(),
            }
            value = int(self.env['ir.config_parameter'].sudo().get_param('antareja_mobile_token.expires_in')) or (60*60*24)
            if value:
                expires = datetime.now() + timedelta(seconds=value)
                vals['expires'] = expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
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
