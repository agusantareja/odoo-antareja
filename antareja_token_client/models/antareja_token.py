# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccessToken(models.Model):
    _inherit = 'antareja.token'

    def client_token_validation(self, token):
        # client_api
        client_id = self.env['client.api'].sudo().search([('token', '=', token)], limit=1)
        if client_id:
            _logger.error("Token is not valid!")
            return True
        return super(AccessToken, self).client_token_validation(token)
