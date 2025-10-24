# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class ApprovalTransactionView(models.AbstractModel):
    _name = "approval.transaction.view.able.mixin"
    _inherit = "approval.transaction.able.mixin"

    view_name = fields.Char()

    def action_approval_transaction(self):
        if not self:
            raise UserError("No Approval")

        rec = self.ensure_one()
        if not rec.transaction_model_name or not rec.transaction_id:
            raise UserError("No Transaction")

        win_dict = super(ApprovalTransactionView, self).action_approval_transaction()
        model = self.env['ir.model'].search([('model', '=', rec.transaction_model_name)], limit=1)
        win_dict['name'] = model.name
        if rec.view_name:
            obj_ir_view = self.env["ir.ui.view"]
            obj_ir_view_browse = obj_ir_view.sudo().search(
                [("name", "=", rec.view_name), ("model", "=", rec.transaction_model_name)],
                limit=1
            )
            if obj_ir_view_browse:
                win_dict['view_id'] = obj_ir_view_browse.id
        return win_dict
