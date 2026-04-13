# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import jwt
import time
import logging

_logger = logging.getLogger(__name__)


class ApplicationServerAuth(models.Model):
    _name = 'application.server.auth'
    _inherit = ['ir.config_parameter.able.mixin', 'client.auth.mixin']

    active = fields.Boolean(default=True)
    name = fields.Char()
    application_server_id = fields.Many2one('application.server')
    application_server_path_ids = fields.One2many('application.server.path', 'application_server_auth_id')

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
        return super(ApplicationServerAuth, self).get_token_endpoint_url() or f"{self.get_endpoint_url()}{self.rest_login_path()}"

    def get_application_name(self):
        return self.application_server_id.name

    def get_endpoint_url(self):
        return self.application_server_id.get_endpoint_url()

    def is_jwt(self):
        try:
            jwt.get_unverified_header(self.access_token)
            return True
        except jwt.InvalidTokenError:
            return False

    def is_token_expired(self):
        payload = jwt.decode(
            self.access_token,
            options={"verify_signature": False}
        )
        exp = payload.get("exp")
        if not exp:
            return True  # tidak ada exp → anggap expired

        now = int(time.time())
        return now >= exp
