from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
import datetime
import logging
import json
import requests

_logger = logging.getLogger(__name__)


class CompensatoryRequest(models.Model):
    _name = "leave.compensatory_request"
    _inherit = [_name, 'approval.transaction.mixin', 'mail.template.internal.mixin']

    stage_inline_cr_id = fields.Many2one(
        'approval.transaction.stage'
    )

    def get_requester_id(self):
        return self.ensure_one().employee_id.user_id.id

    def set_starting_status_approval(self):
        """
        Starting status approval
        """
        self.set_transaction_status('submitted')

    def button_submit(self):
        for rec in self:
            rec.reset_line_approval()
            rec.validate_before_change_state('draft', 'submitted')
            rec.strategy_button_submit()
            approval_obj = self.env['leave.compensatory_request_approval'].sudo().search(
                [('cr_id', '=', rec.id), ('status', '=', 'waiting_approval')])
            if not approval_obj:
                context = "compensatory"
                rec.update_compensatory_request(context)

    def reset_line_approval(self):
        """
        Bila pernah di reject perlu di reset
        """
        self.ensure_one()
        if not self.leave_approval_ids or self.leave_approval_ids.filtered(lambda f: f.status_approval == 'rejected'):
            self.write({ 'leave_approval_ids': False,})
            self.append_approval()

    def validate_before_change_state(self, from_state, to_state):
        rec = self.ensure_one()

        if not rec.line_id:
            raise ValidationError(_("Date Harus Diisi"))

    def callback_approval_stage_rejected(self, approval_stage):
        super().callback_approval_stage_rejected(approval_stage)
        message = "Note Reject => %s" % (self.env.context.get('__reject_reason'))
        # mail bot
        self.write({
                'flag_note': True,
                'notes': message + " by " + str(self.env.user.partner_id.name)
        })


    def get_access_button(self):
        for rec in self:
            rec.access_button = self.access_approval

    def _get_approval_requests(self):
        return {
            'domain': [('access_approval', '=', True), ('state', '=', 'submitted')],
            #'domain': [('id', 'in', data)],
            'view_mode': 'tree,form,kanban',
            'res_model': self._name,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'name': _('To Approve'),
            # 'res_id': self.id,
            'target': 'current',
            'context': {
                'create': 0,
                'delete': 0
            }
        }
