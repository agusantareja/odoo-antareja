# -*- coding: utf-8 -*-

import logging
import requests

from odoo import models, fields, api
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class AntarejaTokenIssuer(models.Model):
    _name = 'antareja.token.issuer'
    _description = 'Antareja Token Issuer'
    _order = 'sequence, name'

    sequence = fields.Integer(default=10)
    name = fields.Char('Issuer', required=True, help='Issuer Name')
    issuer_type = fields.Selection([('token-trusted', 'Token Trusted')], string='Issuer Type', required=True, default='jwt')
    auth_endpoint = fields.Char('Authentication URL')  # OAuth provider URL to authenticate users
    validation_endpoint = fields.Char('Validation URL')  # OAuth provider URL to validate tokens
    data_endpoint = fields.Char('Data URL')

    def validate(self, token, payload=None):
        if self.issuer_type == 'token-trusted':
            validation = self._auth_oauth_validate(token)
            if not validation.get('user_id'):
                # Workaround: facebook does not send 'user_id' in Open Graph Api
                if validation.get('id'):
                    validation['user_id'] = validation['id']
                else:
                    raise AccessDenied()
            return validation
        return {}

    @api.model
    def _auth_oauth_rpc(self, endpoint, access_token):
        header = {'Authorization': f"Bearer {access_token}"}
        param = {'access_token': access_token}
        res = requests.get(endpoint, headers=header, params=param)
        return res.json()

    @api.model
    def _auth_oauth_validate(self, access_token):
        """ return the validation data corresponding to the access token """
        validation = self._auth_oauth_rpc(self.validation_endpoint, access_token)
        if validation.get("error"):
            raise Exception(validation['error'])
        if self.data_endpoint:
            data = self._auth_oauth_rpc(self.data_endpoint, access_token)
            validation.update(data)
        return validation
