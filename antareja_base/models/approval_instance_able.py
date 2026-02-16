from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError, ValidationError
import logging

_logger = logging.getLogger(__name__)


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


class ApprovalInstanceAbleMixin(models.AbstractModel):
    _name = 'approval.instance.able.mixin'
    _inherit = "approval.transaction.task.able.mixin"

    approval_instance_id = fields.Many2one(
        'approval.instance',
        compute="compute_approval_instance_id"
    )
    access_approval = fields.Boolean(
        compute="compute_access_approval",
        search="search_filter_access_approval",
    )
    flag_reject = fields.Boolean()
    note_reject = fields.Text()

    @api.depends_context("uid")
    @api.depends('approval_instance_id')
    def compute_access_approval(self):
        for rec in self:
            rec.access_approval = rec.approval_instance_id.access_approval

    def search_filter_access_approval(self, operator, value):
        datas = self.search([])
        ids= [data.id for data in datas if data.access_approval]
        return [('id','in',ids)]

    def action_ensure_approval_instance(self):
        rec = self.ensure_one()
        approval_instance = rec.approval_instance_id.create_or_get(transaction=rec)
        return {
            'type': 'ir.actions.act_window',
            'name': self._name,
            'res_model': approval_instance._name,
            'res_id': approval_instance.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'create': 0,
                'edit': 0,
            }
        }
    def ensure_approval_instance(self):
        rec = self.ensure_one()
        return rec.approval_instance_id.create_or_get(transaction=rec)

    def action_request_approval(self):
        rec = self.ensure_one()
        approval_instance = rec.approval_instance_id.create_or_get(rec)
        return approval_instance.request_approval()

    def action_approve(self):
        rec = self.ensure_one()
        approval_instance = rec.approval_instance_id.create_or_get(rec)
        return approval_instance.action_approve()

    def action_reject(self):
        rec = self.ensure_one()
        approval_instance = rec.approval_instance_id.create_or_get(rec)
        return approval_instance.action_reject()

    def reject_from_popup_reject(self,**kwargs):
        rec = self.ensure_one()
        approval_instance = rec.approval_instance_id.create_or_get(rec)
        return approval_instance.reject_from_popup_reject(**kwargs)

    def action_clear_approval(self):
        rec = self.ensure_one()
        approval_instance = rec.approval_instance_id.create_or_get(rec)
        return approval_instance.clear_approval()

    def compute_approval_instance_id(self):
        for rec in self:
            rec.approval_instance_id = self.approval_instance_id.search(
                [('model_id.model', '=', self._name), ('transaction_id', '=', rec.id)])

    def get_next_approval_task_line(self):
        rec = self.ensure_one()
        approval_instance = rec.approval_instance_id.create_or_get(rec)
        return approval_instance and approval_instance.get_next_approval_task_line()

    def get_users_approval_notification(self, **kwargs):
        return self.get_next_approval_task_line().get_users_for_notification(**kwargs)

    def send_approval_notification(self, **kwargs):
        rec = self.ensure_one()
        notification_template = kwargs.get(
            "notification_template") or rec.approval_instance_id.get_notification_approval()
        users = kwargs.get("users") or rec.get_users_for_notification(**kwargs)
        if notification_template:
            notification_template.send_notification_to_users(users, rec.id, **kwargs)

    def unregister_approval_task(self, **kwargs):
        """
        Approval task as done
        """
        self.ensure_one()
        self.env['approval.instance'].create_or_get(self).unregister_approval_task_line(**kwargs)
        super(ApprovalInstanceAbleMixin, self).unregister_approval_task(**kwargs)

    def is_status_waiting_approval(self):
        rec = self.ensure_one()
        approval_instance = rec.approval_instance_id.create_or_get(rec)
        return approval_instance.is_status_waiting_approval()

    def get_all_approval_task_line(self):
        return self.approval_instance_id.get_all_approval_task_line()