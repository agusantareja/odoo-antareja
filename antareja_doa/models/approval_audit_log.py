from odoo import models, fields, api


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))



class ApprovalAuditLog(models.Model):
    _inherit = 'approval.audit.log'
    delegatee_user_id = fields.Many2one('res.users', string="Acting User")
    delegator_user_id = fields.Many2one('res.users', string="On Behalf Of")
    user_delegate_id = fields.Many2one('user.delegate', string="Delegate Rule")
    # def send_message(self):
    #     super().send_message()
    #     rec = self.ensure_one()
    #     if self.approval_task_id:
    #         if self.action_type == 'proxy_reject':
    #             message = self.approval_task_id.get_reject_comment_message()
    #         elif rec.action_type == 'proxy_approve':
    #             message = self.approval_task_id.get_approved_comment_message()
    #         else:
    #             return
    #         self.approval_task_id.notify_transaction_comment(message=message)

    def create_audit_log(self, **kwargs):
        kw = dict(kwargs)
        if kwargs.get('user_delegate'):
            kw['user_delegate_id']= int(kwargs.get('user_delegate'))

        return super(ApprovalAuditLog, self).create_audit_log(kw)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'user_delegate_id' in vals:
                user_delegate = self.user_delegate_id.browse(vals['user_delegate_id'])
                if not vals.get('delegatee_user_id'):
                    vals['delegatee_user_id'] = user_delegate.delegatee_id.id
                if not vals.get('delegator_user_id'):
                    vals['delegator_user_id'] = user_delegate.delegator_id.id

        return super(ApprovalAuditLog, self).create(vals_list)
