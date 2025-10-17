# -*- coding: utf-8 -*-
from ..tools.utils import get_email_template_rejection_id, get_mail_bot_template_approval_id, \
    get_mail_bot_template_rejection_id, get_whatsapp_template_rejection_id, get_whatsapp_template_approval_id
from ..tools.utils import to_integer, have_method, get_company_id, get_transaction_menu_id, \
    get_requester_id, render_jinja, get_email_template_approval_id
from odoo import models, fields, api, _

_logger = __import__('logging').getLogger(__name__)


class AbstractApprovalStageNotification(models.AbstractModel):
    _name = "abstract.approval.stage.notification"
    _description = """
    Notification config
    """
    # setup when configuration
    notification_template_approval_id = fields.Many2one(
        'notification.template',
        string='Mail Bot Template Approval',
        help="Notification template used for approval notifications."
    )
    notification_template_rejection_id = fields.Many2one(
        'notification.template',
        string='Mail Bot Template Approval',
        help="Notification template used for reject notifications.")

    # mail_bot_template_rejection_id = fields.Many2one(
    #     'mail.template', string='Mail Bot Template Rejection',
    #     help="Email template used for rejection notifications.")
    #
    # email_template_approval_id = fields.Many2one(
    #     'mail.template', string='Email Template Approval',
    #     help="Email template used for approval notifications.")
    #
    # email_template_rejection_id = fields.Many2one(
    #     'mail.template', string='Email Template Rejection',
    #     help="Email template used for rejection notifications.")
    #
    # whatsapp_template_approval_id = fields.Many2one(
    #     'mail.template', string='Whatsapp Template Approval',
    #     help="Email template used for approval notifications.")
    #
    # whatsapp_template_rejection_id = fields.Many2one(
    #     'mail.template', string='Whatsapp Template Rejection',
    #     help="Email template used for rejection notifications.")


class AbstractApprovalNotification(models.AbstractModel):
    _name = "approval.notification.task.mixin"
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

    # approve
    def get_notification_template_approval_task(self, **kwargs):
        template = self.env.ref('antareja_approval.notification_template_approval_task')
        return template, self.id

    # def get_email_template_approval_task(self, **kwargs):
    #     template = self.env.ref('antareja_approval.mail_template_email_notification_approval_task')
    #     return template, self.id

    def notify_approval_by_users(self, users, **kwargs):
        if self.env.context.get('__ignore_notify_approval_by_users') or not users:
            return
        template, res_id = self.get_notification_template_approval_task(**kwargs)
        if template:
            template.send_notification_to_users(users,res_id)
        else:
            _logger.warning("No notification template found for approval notification.")

    # reject
    def get_notification_template_rejection_task(self, **kwargs):
        template = self.env.ref('antareja_approval.notification_template_approval_task')
        return template, self.id

    # def get_email_template_rejection_task_user(self, **kwargs):
    #     template = self.env.ref('antareja_approval.mail_template_email_notification_rejection_task')
    #     return template, self.id

    def notify_reject_task_users(self, users, **kwargs):
        if self.env.context.get('__ignore_notify_rejected_by_users') or not users:
            return
        template, res_id = self.get_notification_template_rejection_task(**kwargs)
        if template:
            template.send_notification_to_users(users,res_id)
        else:
            _logger.warning("No notification template found for approval notification.")

    def notify_reject_task_user(self, requester, **kwargs):
        self.notify_reject_task_users(requester, **kwargs)


    # transaction comment
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

    def notify_transaction_comment(self, message=None):
        transaction_object = self.get_transaction_object()
        if not transaction_object or not message:
            return
        user = self.env.user
        self.env['mail.message'].sudo().create({
            'model': transaction_object._name,
            'res_id': transaction_object.id,
            'message_type': 'comment',
            'author_id': user.partner_id.id,
            'date': fields.Datetime.now(),
            'body': message,
        })
