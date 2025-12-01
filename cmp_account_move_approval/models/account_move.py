# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from odoo.tools import formatLang, float_compare


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = [_name, 'cni.approval.transaction.task.able.mixin']

    state = fields.Selection(selection_add=[
        ('waiting_approval', 'Waiting Approval'),
    ], ondelete={'waiting_approval': 'cascade'}, )

    # add state for approva
    approval_state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('posted', 'Posted'),
    ], string='Approval Status',
        default='draft'
    )

    move_need_approval = fields.Boolean(compute="_compute_move_need_approval")
    move_readonly = fields.Boolean(compute="_compute_move_readonly")

    cni_approval_instance_id = fields.Many2one(
        'cni.approval.instance',
        compute="compute_cni_approval_instance_id"
    )
    cni_approval_line = fields.Many2many(
        'cni.approval.transaction',
        compute="compute_cni_approval_instance_id"
    )

    @api.depends('journal_id.approval_matrix_id')
    def _compute_move_need_approval(self):
        for rec in self:
            rec.move_need_approval = rec.journal_id.approval_matrix_id

    @api.depends('state', 'approval_state', 'move_need_approval')
    def _compute_move_readonly(self):
        for record in self:
            record.move_readonly = record.state != 'draft' or (
                    record.move_need_approval and record.approval_state != 'draft')

    def compute_cni_approval_instance_id(self):
        for rec in self:
            rec.cni_approval_instance_id = self.cni_approval_instance_id.search(
                [('model_id.model', '=', self._name), ('transaction_id', '=', rec.id)])

            rec.cni_approval_line = rec.cni_approval_instance_id.cni_approval_line

    def get_next_approval_transaction(self):
        rec = self.ensure_one()
        cni_approval_instance = rec.cni_approval_instance_id.create_or_get(rec)
        return cni_approval_instance and cni_approval_instance.get_next_approval_transaction() or self.env[
            'cni.approval.transaction'].browse()

    def get_users_approval_notification(self, **kwargs):
        return self.get_next_approval_transaction().get_users_approval_notification(**kwargs)

    def validate_request_approval(self,approval_instance=None):
        """Validate the documents. before request approval
        this code copy form _post
        """

        for invoice in self.filtered(lambda move: move.is_invoice(include_receipts=True)):
            if (
                    invoice.quick_edit_mode
                    and invoice.quick_edit_total_amount
                    and invoice.currency_id.compare_amounts(invoice.quick_edit_total_amount, invoice.amount_total) != 0
            ):
                raise UserError(_(
                    "The current total is %s but the expected total is %s. In order to post the invoice/bill, "
                    "you can adjust its lines or the expected Total (tax inc.).",
                    formatLang(self.env, invoice.amount_total, currency_obj=invoice.currency_id),
                    formatLang(self.env, invoice.quick_edit_total_amount, currency_obj=invoice.currency_id),
                ))
            if invoice.partner_bank_id and not invoice.partner_bank_id.active:
                raise UserError(_(
                    "The recipient bank account linked to this invoice is archived.\n"
                    "So you cannot confirm the invoice."
                ))
            if float_compare(invoice.amount_total, 0.0, precision_rounding=invoice.currency_id.rounding) < 0:
                raise UserError(_(
                    "You cannot validate an invoice with a negative total amount. "
                    "You should create a credit note instead. "
                    "Use the action menu to transform it into a credit note or refund."
                ))

            if not invoice.partner_id:
                if invoice.is_sale_document():
                    raise UserError(
                        _("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
                elif invoice.is_purchase_document():
                    raise UserError(
                        _("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

            # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
            # lines are recomputed accordingly.
            if not invoice.invoice_date:
                if invoice.is_sale_document(include_receipts=True):
                    invoice.invoice_date = fields.Date.context_today(self)
                elif invoice.is_purchase_document(include_receipts=True):
                    raise UserError(_("The Bill/Refund date is required to validate this document."))

            if not invoice.date and invoice.is_purchase_document(include_receipts=True):
                raise UserError(_("The Bill/Refund date is required to validate this document."))

        for move in self:
            if move.state == 'posted':
                raise UserError(_('The entry %s (id %s) is already posted.') % (move.name, move.id))
            if not move.line_ids.filtered(lambda line: line.display_type not in ('line_section', 'line_note')):
                raise UserError(_('You need to add a line before posting.'))
            if not move.journal_id.active:
                raise UserError(_(
                    "You cannot post an entry in an archived journal (%(journal)s)",
                    journal=move.journal_id.display_name,
                ))
            if move.display_inactive_currency_warning:
                raise UserError(_(
                    "You cannot validate a document with an inactive currency: %s",
                    move.currency_id.name
                ))

            if move.line_ids.account_id.filtered(lambda account: account.deprecated):
                raise UserError(_("A line of this move is using a deprecated account, you cannot post it."))

        for expense in self.filtered(lambda move: move.is_expense_claim()):
            if not expense.partner_id:
                raise UserError(_("The field 'Employee' is required, please complete it to validate the Expense Claim."))
            if not expense.invoice_date:
                raise UserError(_("The Expense Claim date is required to validate this document."))

    def event_approval_start(self,**kwargs):
        rec = self.ensure_one()
        rec.write({
            'state':'waiting_approval',
            'approval_state': 'waiting_approval',
        })

    def event_approval_done(self,**kwargs):
        rec = self.ensure_one()
        if rec.approval_state=='approved':
            rec.action_post()

def get_users_signature(self):
        rec = self.ensure_one()
        users_signature= [
            {
                'sign_title': 'Created by',
                'sign_user': rec.create_uid
            },
            # {
            #     'sign_title': 'Verified by',
            # },
            # {
            #     'sign_title': 'Approved by',
            # },
        ]

        for line in rec.cni_approval_instance_id.approval_line:
            users_signature.append({
                'sign_title': 'Approved by',
                'sign_user': line.user_execution_id
            })

        return users_signature
