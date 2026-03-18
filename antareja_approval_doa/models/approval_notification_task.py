# -*- coding: utf-8 -*-

import os
from odoo import models, fields, api, _
import logging
from odoo.exceptions import ValidationError, UserError
from ..tools.utils import ignore_delegated_user_context, to_integer, get_email_template_approval_id, \
    get_mail_bot_template_approval_id, get_whatsapp_template_approval_id, get_requester_id, \
    get_email_template_rejection_id, get_mail_bot_template_rejection_id, get_whatsapp_template_rejection_id

from ..tools.utils import to_integer, get_company_id, have_method
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class AbstractApprovalNotification(models.AbstractModel):
    _inherit = "approval.notification.task.mixin"
    _description = """
    Mixin : Approval Notification Approval Task Model
    """
    # comment
    def get_approved_comment_message(self, **kwargs):
        user_id = kwargs.get('user_id') or kwargs.get('user') or self.env.user
        user = self.get_object_model(user_id, 'res.users')
        user_delegate_id = kwargs.get('user_delegate_id') or self.env.context.get("__user_delegate_id")
        user_delegate = self.get_object_model(user_delegate_id, 'user.delegate')
        if user_delegate:
            proxy_user = user_delegate.proxy_id
            delegator_user = user_delegate.delegator_id
            message = "Approved oleh  %s (atas nama %s) pada tanggal %s ." % (
                proxy_user.name, delegator_user.name, fields.Date.today().strftime("%d-%m-%Y"))
        else:
            message = "Approved => oleh %s pada tanggal %s ." % (
                user.name, fields.Date.today().strftime("%d-%m-%Y"))
        return message

    def get_reject_comment_message(self, **kwargs):
        user_id = kwargs.get('user_id') or kwargs.get('user') or self.env.user
        user = self.get_object_model(user_id, 'res.users')
        user_delegate_id = kwargs.get('user_delegate_id') or self.env.context.get("__user_delegate_id")
        user_delegate = self.get_object_model(user_delegate_id, 'user.delegate')
        reject_reason = kwargs.get('reject_reason') or kwargs.get('reason_approval') or self.env.context.get(
            "__reject_reason") or "No reason provided"
        if user_delegate:
            proxy_user = user_delegate.proxy_id
            delegator_user = user_delegate.delegator_id
            message = "Reject oleh  %s (atas nama %s) pada tanggal %s , reason: %s" % (
                proxy_user.name, delegator_user.name, fields.Date.today().strftime("%d-%m-%Y"), reject_reason)
        else:
            message = "Reject => oleh %s pada tanggal %s , reason: %s" % (
                user.name, fields.Date.today().strftime("%d-%m-%Y"), reject_reason)
        return message

    def notify_transaction_comment(self,message=None):
        self.env['mail.queue_job'].transaction_comment(
            self.get_transaction_object(), self.env.user, message=message)
