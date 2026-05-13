# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccessToken(models.Model):
    _inherit = 'antareja.token'

    def validate(self, token, refresh_token=False):
        if not refresh_token:
            res = self.env['res.users'].sudo().search([('oauth_access_token', '=', token)], limit=1)
            if res.oauth_provider_id:
                payload = res._auth_oauth_validate(res.oauth_provider_id.id, token)
                payload['uid'] = res.id
                payload['username'] = res.login
                return payload
        return super(AccessToken, self).validate(token, refresh_token=refresh_token)
