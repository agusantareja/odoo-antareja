from odoo import models, fields, api


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


class AbstractApprovalAuditLog(models.AbstractModel):
    _inherit = 'abstract.approval.audit.log'
    _description = 'Approval Audit Log'
    _order = 'create_date desc'

    proxy_user_id = fields.Many2one('res.users', string="Acting User")
    delegator_user_id = fields.Many2one('res.users', string="On Behalf Of")
    user_delegate_id = fields.Many2one('user.delegate', string="Delegate Rule")


class ApprovalAuditLog(models.Model):
    _inherit = 'approval.audit.log'

    def send_message(self):
        super().send_message()
        rec = self.ensure_one()
        if self.approval_task_id:
            if self.action_type == 'proxy_reject':
                message = self.approval_task_id.get_reject_comment_message()
            elif rec.action_type == 'proxy_approve':
                message = self.approval_task_id.get_approved_comment_message()
            else:
                return
            self.approval_task_id.notify_transaction_comment(message=message)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'user_delegate_id' in vals:
                user_delegate = self.user_delegate_id.browse(vals['user_delegate_id'])
                if not vals.get('proxy_user_id'):
                    vals['proxy_user_id'] = user_delegate.proxy_id.id
                if not vals.get('delegator_user_id'):
                    vals['delegator_user_id'] = user_delegate.delegator_id.id

        return super(ApprovalAuditLog, self).create(vals_list)
