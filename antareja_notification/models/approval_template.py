# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.exceptions import UserError
from odoo.tools import *
from odoo.tools.safe_eval import safe_eval, test_python_expr

import base64
import logging

from pytz import timezone

_logger = logging.getLogger(__name__)


class ApprovalTemplateMixin(models.AbstractModel):
    _inherit = 'approval.template.mixin'

    notification_approval_id = fields.Many2one(
        'notification.template',
        help="Notification template used for approval notifications."
    )
    notification_rejection_id = fields.Many2one(
        'notification.template',
        help="Notification template used for reject notifications."
    )
    notification_approved_id = fields.Many2one(
        'notification.template',
        help="Notification template used for reject notifications."
    )

    def get_notification_approval(self):
        return self.notification_approval_id

    def get_notification_rejection(self):
        return self.notification_rejection_id

    def get_notification_approved(self):
        return self.notification_approved_id