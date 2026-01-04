# -*- coding: utf-8 -*-

import logging
import uuid

from odoo import models, fields, api


_logger = logging.getLogger(__name__)


class AccessToken(models.Model):
    _name = 'antareja.refresh.token'
    _description = "JWT Refresh Token"

    token = fields.Char(required=True, index=True)
    user_id = fields.Many2one(
        "res.users",
        required=True,
        ondelete="cascade"
    )
    expires_at = fields.Datetime(required=True)
    revoked = fields.Boolean(default=False)

    _sql_constraints = [
        ("token_unique", "unique(token)", "Refresh token must be unique")
    ]

    @staticmethod
    def generate_token():
        return str(uuid.uuid4())
