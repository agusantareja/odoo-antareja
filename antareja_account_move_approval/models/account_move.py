# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class UserDelegate(models.Model):
    _name = 'account.move'
    _inherit = [
        _name,
        'approval.transaction.mixin','mail.template.internal.mixin'
    ]

    # add state for approva
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
    ], string='Approval Status', default='draft', tracking=True)

    move_need_approval = fields.Boolean(compute="_compute_move_need_approval")

    @api.depends('journal_id')
    def _compute_move_need_approval(self):
        for rec in self:
            rec.move_need_approval = rec.journal_id.approval_template_id

    def validate_request_approval(self):
        pass

    def action_request_approval(self):
        self.validate_request_approval()

        for rec in self:
            if rec.state=='draft' and rec.move_need_approval and rec.approval_state=='draft' :
                rec.strategy_button_submit()

    def action_approve(self):
        for rec in self:
            rec.approval_state = 'approved'

    def action_post(self):
        # prevent posting if not approved
        for rec in self:
            if rec.move_need_approval and rec.approval_state != 'approved':
                raise UserError("Bill must be approved before posting.")
        return super().action_post()

    def get_transaction_status(self):
        return self.approval_state or 'draft'

    def set_transaction_status(self, status):
        self.write({'approval_state': status})

    def get_number_invoice(self):
        if self.invoice_sequence_number_next_prefix and self.name=='/':
            return f"{self.invoice_sequence_number_next_prefix}/{self.invoice_sequence_number_next}"
        else:
            return self.name
