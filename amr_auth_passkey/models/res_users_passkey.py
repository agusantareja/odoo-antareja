# -*- coding: utf-8 -*-

import logging
import jwt

from jwt import InvalidTokenError
from odoo import api, fields, models
from odoo.http import request

_logger = logging.getLogger(__name__)

from odoo import models, fields


class ResUsersPasskey(models.Model):
    _name = 'res.users.passkey'

    user_id = fields.Many2one('res.users', required=True)
    credential_id = fields.Char(required=True)
    public_key = fields.Text(required=True)
    sign_count = fields.Integer(default=0)
    transports = fields.Char()
    name = fields.Char()
