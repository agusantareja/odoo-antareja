# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from datetime import datetime, timedelta
import jwt
import time
from jwt import ExpiredSignatureError, InvalidTokenError, InvalidAudienceError
from odoo.exceptions import AccessDenied
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class AccessToken(models.Model):
    _inherit = 'antareja.token'

    def get_provider_id(self, access_token):
        # todo
        return 0

    def validate(self, token, refresh_token=False):
        if not refresh_token:
            res = self.env['res.users'].sudo().search([('oauth_access_token', '=', token)],limit=1)
            if res:
                provider_id=res.oauth_provider_id.id
            else:
                provider_id = self.get_provider_id(token)
            if provider_id:
                (db,login,access_token) = self.env['res.users'].auth_oauth(provider_id,{'access_token':token})
                res = self.env['res.users'].sudo().search([('login', '=', login)], limit=1)
                try:
                    payload = jwt.decode(
                        access_token,
                    )
                    payload['uid'] = res.id
                    return payload
                except InvalidAudienceError:
                    return None
                except ExpiredSignatureError:
                    return None
                except InvalidTokenError:
                    return None
        return super(AccessToken,self).validate(token,refresh_token=refresh_token)