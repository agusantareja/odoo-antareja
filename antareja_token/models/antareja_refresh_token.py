# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
import uuid
from datetime import datetime, timedelta
from jwt import ExpiredSignatureError, InvalidTokenError, InvalidAudienceError
from odoo.exceptions import AccessDenied
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

# try:
#     from oauthlib import common as oauthlib_common
# except ImportError:
#     _logger.warning(
#         'OAuth library not found. If you plan to use it, '
#         'please install the oauth library from '
#         'https://pypi.python.org/pypi/oauthlib')


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
