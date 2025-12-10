 # -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api
from datetime import datetime, timedelta

from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    mobile_access_ids = fields.One2many(
        'mobile.access.token', 'user_id', string="Access Tokens")

    def action_mobile_access_token(self):
        self.mobile_access_ids._get_access_token(user_id=self.id, create=True)

    def get_mobile_access_token(self,create=False):
        return self.mobile_access_ids._get_access_token(user_id=self.id, create=create)

    def _check_credentials(self, password):
        try:
            return super(ResUsers, self)._check_credentials(password)
        except AccessDenied:
            res = self.mobile_access_ids.sudo().search([('user_id', '=', self.env.uid), ('token', '=', password)])
            if not res or res.is_expired():
                raise
