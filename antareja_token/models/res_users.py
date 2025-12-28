# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from datetime import datetime, timedelta

from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def get_mobile_access_token(self, create=False):
        return self.get_access_token(user_id=self.id, create=create)

    def get_access_token(self, create=False):
        return self.get_access_token(user_id=self.id, create=create)

    def _check_credentials(self, password):
        try:
            return super(ResUsers, self)._check_credentials(password)
        except AccessDenied:
            payload = self.env['antareja.token'].validate(password)
            if not payload or payload.get('uid') != self.id:
                raise
