# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools

import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def get_notification_user_ids(self, company_id=None):
        """
        Override method to return the user itself as a notification recipient.
        This is useful for cases where the user needs to receive notifications
        about their own actions or changes.
        """

        uid = self.id
        if uid and uid != self._uid:
            self = self.with_user(uid)

        return self.env['user.delegate'].get_notification_user_ids(user_ids=[self._uid],company_id=company_id)
