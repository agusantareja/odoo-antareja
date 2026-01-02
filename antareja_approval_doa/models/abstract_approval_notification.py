# -*- coding: utf-8 -*-
from odoo.addons.antareja_approval.tools.utils import to_integer, get_company_id, have_method
from odoo import models, fields, api, _

_logger = __import__('logging').getLogger(__name__)


class AbstractApprovalNotification(models.AbstractModel):
    _inherit = "abstract.approval.notification"

    # def notify_approval_by_users(self, users, **kwargs):
    #     transaction_object = (kwargs.get('transaction_object') or self.get_transaction_object(**kwargs))
    #     if transaction_object and 'transaction_object' not in kwargs:
    #         kwargs['transaction_object'] = transaction_object
    #     company_id = to_integer(kwargs.get('company_id') or get_company_id(transaction_object))
    #     user_ids = [user.id for user in users]
    #     proxy_ids = self.env['user.delegate'].get_all_proxy_ids_for_delegator_ids(user_ids, company_id=company_id)
    #     users = self.env['res.users'].browse(user_ids+proxy_ids)
    #     super(AbstractApprovalNotification, self).notify_approval_by_users(users, **kwargs)

    def get_proxy_partner(self, **kwargs):
        """
        Method to get the proxy partner ID.
        This method should be implemented in the inheriting model.
        """
        rec_object = kwargs.get('rec_object') or self.ensure_one()
        proxy_partner = kwargs.get('proxy_partner_id')
        if not proxy_partner and have_method(rec_object, "get_proxy_partner"):
            proxy_partner_id = rec_object.get_proxy_partner()
        return to_integer(proxy_partner_id)

    def get_approved_transaction_comment_message(self, **kwargs):
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

    def get_reject_transaction_comment_message(self, **kwargs):
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

    def reject_transaction_comment(self, **kwargs):
        rec_object = kwargs.get('rec_object') or self.ensure_one()
        if not rec_object:
            raise ValueError("rec_object is required for reject_transaction_comment method.")
        proxy_partner_id = kwargs.get('proxy_partner_id')
        partner_id = proxy_partner_id or kwargs.get('partner_id') or self.env.user.partner_id.id
        message = kwargs.get('message')
        message = message or self.get_reject_transaction_comment_message(rec_object=rec_object, **kwargs)
        self.env['mail.message'].sudo().create({
            'model': rec_object._name,
            'res_id': to_integer(rec_object),
            'message_type': 'comment',
            'author_id': to_integer(partner_id),
            'date': fields.Datetime.now(),
            'body': message,
        })
