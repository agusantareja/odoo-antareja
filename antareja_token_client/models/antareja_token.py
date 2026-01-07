# -*- coding: utf-8 -*-

import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class AccessToken(models.Model):
    _inherit = 'antareja.token'

    def validate(self, access_token, refresh_token=False):
        try:
            result = super(AccessToken,self).validate(access_token,refresh_token=refresh_token)
        except Exception as e:
            result=None
        if result and not refresh_token:
            access_token_data = self.env['oauth.access_token'].sudo().search([('token', '=', access_token)], order='id DESC', limit=1)
            if access_token_data._get_access_token_google(employee_id=access_token_data.employee_id.id) != access_token:
                user = access_token_data.employee_id
                epoch_unix = None
                if access_token_data.expires:
                    epoch_timestamp = fields.Datetime.to_datetime(access_token_data.expires).timestamp()
                    epoch_unix = int(epoch_timestamp)
                result = {
                    'uid': user.id,
                    'login': user.login,
                    'sub':user.login,
                    'email':user.email,
                    'exp':epoch_unix,
                    'token': access_token,
                }
        return result

    def client_token_validation(self,token):
        # client_api
        client_id = self.env['client.api'].sudo().search([('token', '=', token)], limit=1)
        if  client_id:
            _logger.error("Token is not valid!")
            return True
        return super(AccessToken,self)
