# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError
from odoo.models import BaseModel
import logging

_logger = logging.getLogger(__name__)


class ApprovalTaskLine(models.Model):
    _name = 'approval.task.line'
    _inherit = ['approval.task.line.mixin',
                'abstract.approval.status',
                'abstract.approval.access',
                'approval.transaction.view.able.mixin'
                ]
    _description = 'This is Approval Task Line for Approval helper waiting approval'
    _order = 'id'
    approval_instance_id = fields.Many2one('approval.instance')
    requester_id = fields.Many2one(
        'res.users', 'Requester',
        default=lambda self: self.env.user,
        help="User who requested the approval."
    )
    reject_to_method = fields.Selection(default='to_requestor')
    user_execution_id = fields.Many2one(
        'res.users',
        'User Execution',
        help="User who executed approval (Approve/Reject)the transaction"
    )
    date_execution = fields.Datetime('Date Execution')
    reject_reason = fields.Text('Reject Reason')


    def set_approved_status(self, **kwargs):
        self.ensure_one()
        self.write({
            'user_execution_id': self.env.uid,
            'date_execution': fields.Datetime.now(),
            'status_approval': 'approved',
        })



    def set_rejected_status(self, **kwargs):
        self.write({
            'user_execution_id':self.env.uid,
            'date_execution': fields.Datetime.now(),
            'status_approval': 'rejected',
            'reject_reason': kwargs.get('reject_reason') or kwargs.get('reason') or self.env.context.get('__reject_reason')
        })

    def set_waiting_status(self, **kwargs):
        self.write({
            'status_approval': 'waiting_approval'
        })

    def get_next_approval_task_line(self,transaction_id = None, transaction_model_name = None):
        transaction_id = transaction_id or self.transaction_id
        transaction_model_name = transaction_model_name or self.transaction_model_name
        next_approval_task_line= self.sudo().search([('transaction_id', '=', transaction_id), ('transaction_model_name', '=', transaction_model_name), ('status_approval', 'in', ['draft','waiting','waiting_approval'])],order='id asc', limit=1)

        if next_approval_task_line and next_approval_task_line.status_approval!='waiting_approval':
            next_approval_task_line.set_waiting_status()
        return next_approval_task_line

    def get_approval_instance(self):
        return self.approval_instance_id


    @api.model
    def action_reject(self):
        return {
            'name': 'Reject Message',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'popup.reject.message.wizard',
            'target': 'new',
        }
