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
    def get_object_model(self, value, model_name):
        """
        Mengembalikan recordset dari value dengan model yang ditentukan.
        value dapat berupa recordset, dict dengan key 'id', string angka, atau integer.
        """
        if not value:
            return self.env[model_name].browse()  # None atau False

        if isinstance(value, models.BaseModel):
            return value

        value_id = None

        if isinstance(value, dict) and 'id' in value:
            value_id = to_integer(value['id'])
        elif isinstance(value, int):
            value_id = value
        elif isinstance(value, str) and value.isdigit():
            value_id = to_integer(value)

        if value_id:
            return self.env[model_name].browse(value_id)

        return self.env[model_name].browse()

    def get_email_template_approval_task(self, **kwargs):
        # task object
        transaction_object = (kwargs.get('transaction_object') or self.get_transaction_object())
        approval_stage_object = (kwargs.get('approval_stage_object') or self.get_approval_stage_object())
        approval_task_object = (kwargs.get('approval_task_object') or self)

        # Ensure the email template is set up in the record
        template_id = (kwargs.get('template_id') or
                       get_email_template_approval_id(approval_stage_object) or
                       get_email_template_approval_id(transaction_object)
                       )
        template = self.get_object_model(template_id, 'mail.template') or self.env.ref('antareja_approval.mail_template_email_notification_approval_task')

        if approval_task_object and template.model == approval_task_object._name:
            return template, approval_task_object.id

        if approval_stage_object and template.model == approval_stage_object._name:
            return template, approval_stage_object.id

        if transaction_object and template.model == transaction_object._name:
            return template, transaction_object.id

        raise UserError("Invalid Configuration email notification approval_task ")

    def get_mail_bot_template_approval_task(self, **kwargs):
        # task object
        transaction_object = (kwargs.get('transaction_object') or self.get_transaction_object())
        approval_stage_object = (kwargs.get('approval_stage_object') or self.get_approval_stage_object())
        approval_task_object = (kwargs.get('approval_task_object') or self)

        # Ensure the email template is set up in the record
        template_id = (kwargs.get('mail_bot_template_id') or
                       get_mail_bot_template_approval_id(approval_stage_object) or
                       get_mail_bot_template_approval_id(transaction_object)
                       )
        template = self.get_object_model(template_id, 'mail.template') or \
               self.env.ref('antareja_approval.mail_template_mail_bot_notification_approval_task')

        if approval_task_object and template.model == approval_task_object._name:
            return template, approval_task_object.id

        if approval_stage_object and template.model == approval_stage_object._name:
            return template, approval_stage_object.id

        if transaction_object and template.model == transaction_object._name:
            return template, transaction_object.id

        raise UserError("Invalid Configuration mail bot notification approval_task ")


    def get_whatsapp_template_approval_task(self, **kwargs):
        # task object
        transaction_object = (kwargs.get('transaction_object') or self.get_transaction_object())
        approval_stage_object = (kwargs.get('approval_stage_object') or self.get_approval_stage_object())
        approval_task_object = (kwargs.get('approval_task_object') or self)
        # Ensure the email template is set up in the record
        template_id = (kwargs.get('whatsapp_template_id') or
                       get_whatsapp_template_approval_id(approval_stage_object) or
                       get_whatsapp_template_approval_id(transaction_object)
                       )

        template = self.get_object_model(template_id, 'mail.template') or \
               self.env.ref('antareja_approval.mail_template_whatsapp_notification_approval_task')

        if approval_task_object and template.model == approval_task_object._name:
            return template, approval_task_object.id

        if approval_stage_object and template.model == approval_stage_object._name:
            return template, approval_stage_object.id

        if transaction_object and template.model == transaction_object._name:
            return template, transaction_object.id

        raise UserError("Invalid Configuration whatapp notification approval_task ")

    def notify_approval_by_users(self,users, **kwargs):
        template, res_id= self.get_email_template_approval_task(**kwargs)
        self.env['mail.queue_job'].send_email_to_user_ids([user.id for user in users], template.id, res_id)

        template, res_id = self.get_mail_bot_template_approval_task(**kwargs)
        self.env['mail.queue_job'].send_mail_bot_to_user_ids([user.id for user in users], template.id, res_id)

        template, res_id = self.get_whatsapp_template_approval_task(**kwargs)
        self.env['mail.queue_job'].send_whatsapp_to_user_ids([user.id for user in users], template.id, res_id)

    # reject
    def get_email_template_rejection_task_user(self, **kwargs):
        transaction_object = (kwargs.get('transaction_object') or self.get_transaction_object())
        approval_stage_object = (kwargs.get('approval_stage_object') or self.get_approval_stage_object())
        approval_task_object = (kwargs.get('approval_task_object') or self)

        # Ensure the email template is set up in the record
        template_id = (kwargs.get('template_id') or
                       get_email_template_rejection_id(approval_stage_object) or
                       get_email_template_rejection_id(transaction_object)
                       )

        template = self.get_object_model(template_id, 'mail.template') or \
               self.env.ref('antareja_approval.mail_template_email_notification_rejection_task')
        if approval_task_object and template.model == approval_task_object._name:
            return template, approval_task_object.id

        if approval_stage_object and template.model == approval_stage_object._name:
            return template, approval_stage_object.id

        if transaction_object and template.model == transaction_object._name:
            return template, transaction_object.id

        raise UserError("Invalid Configuration email notification reject task ")

    def get_mail_bot_template_rejection_task_user(self, **kwargs):
        transaction_object = (kwargs.get('transaction_object') or self.get_transaction_object())
        approval_stage_object = (kwargs.get('approval_stage_object') or self.get_approval_stage_object())
        approval_task_object = (kwargs.get('approval_task_object') or self)

        # Ensure the email template is set up in the record
        template_id = (kwargs.get('mail_bot_template_id') or
                       get_mail_bot_template_rejection_id(approval_stage_object) or
                       get_mail_bot_template_rejection_id(transaction_object)
                       )

        template = self.get_object_model(template_id, 'mail.template') or \
               self.env.ref('antareja_approval.mail_template_mail_bot_notification_rejection_task')

        if approval_task_object and template.model == approval_task_object._name:
            return template, approval_task_object.id

        if approval_stage_object and template.model == approval_stage_object._name:
            return template, approval_stage_object.id

        if transaction_object and template.model == transaction_object._name:
            return template, transaction_object.id

        raise UserError("Invalid Configuration mail bot notification reject task ")

    def get_whatsapp_template_rejection_task_user(self, **kwargs):
        transaction_object = (kwargs.get('transaction_object') or self.get_transaction_object())
        approval_stage_object = (kwargs.get('approval_stage_object') or self.get_approval_stage_object())
        approval_task_object = (kwargs.get('approval_task_object') or self)

        # Ensure the email template is set up in the record
        template_id = (kwargs.get('mail_bot_template_id') or
                       get_whatsapp_template_rejection_id(approval_stage_object) or
                       get_whatsapp_template_rejection_id(transaction_object)
                       )

        template =  self.get_object_model(template_id, 'mail.template') or \
               self.env.ref('antareja_approval.mail_template_whatsapp_notification_rejection_task')

        if approval_task_object and template.model == approval_task_object._name:
            return template, approval_task_object.id

        if approval_stage_object and template.model == approval_stage_object._name:
            return template, approval_stage_object.id

        if transaction_object and template.model == transaction_object._name:
            return template, transaction_object.id

        raise UserError("Invalid Configuration whatsapp notification reject task ")

    def notify_reject_task_user(self, requester, **kwargs):
        template,res_id = self.get_email_template_rejection_task_user(**kwargs)
        self.env['mail.queue_job'].send_email_to_user_ids([requester.id], template.id, res_id)

        template,res_id = self.get_mail_bot_template_rejection_task_user(**kwargs)
        self.env['mail.queue_job'].send_mail_bot_to_user_ids([requester.id], template.id, res_id)

        template,res_id = self.get_whatsapp_template_rejection_task_user(**kwargs)
        self.env['mail.queue_job'].send_whatsapp_to_user_ids([requester.id], template.id, res_id)

    # comment
    def get_approved_comment_message(self, **kwargs):
        user_id = kwargs.get('user_id') or kwargs.get('user') or self.env.user
        user = self.get_object_model(user_id, 'res.users')
        message = "Approved => oleh %s pada tanggal %s ." % (user.name, fields.Date.today().strftime("%d-%m-%Y"))
        return message

    def get_reject_comment_message(self, **kwargs):
        user_id = kwargs.get('user_id') or kwargs.get('user') or self.env.user
        user = self.get_object_model(user_id, 'res.users')
        reject_reason = kwargs.get('reject_reason') or kwargs.get('reason_approval') or self.env.context.get(
            "__reject_reason") or "No reason provided"
        message = "Reject => oleh %s pada tanggal %s : , reason: %s" % (
            user.name, fields.Date.today().strftime("%d-%m-%Y"), reject_reason)
        return message

    def notify_transaction_comment(self,message=None):
        self.env['mail.queue_job'].transaction_comment(
            self.get_transaction_object(), self.env.user, message=message)
