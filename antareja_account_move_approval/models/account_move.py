# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from odoo.tools import formatLang, float_compare


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

    @api.depends('journal_id.approval_template_id')
    def _compute_move_need_approval(self):
        for rec in self:
            rec.move_need_approval = rec.journal_id.approval_template_id

    def validate_request_approval(self):
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


    def action_request_approval(self):
        self.validate_request_approval()

        for rec in self:
            if rec.state=='draft' and rec.move_need_approval and rec.approval_state=='draft' :
                rec.ensure_number_invoice_setup()
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

    def ensure_number_invoice_setup(self):
        move=self.ensure_one()
        move_has_name = move.name and move.name != '/'
        if move.date and (not move_has_name or not move._sequence_matches_date()):
            move._set_next_sequence()


    def get_number_invoice(self):
        if self.invoice_sequence_number_next_prefix and self.name=='/':
            return f"{self.invoice_sequence_number_next_prefix}/{self.invoice_sequence_number_next}"
        else:
            return self.name
