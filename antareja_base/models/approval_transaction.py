# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class ApprovalTransaction(models.AbstractModel):
    _name = "approval.transaction.able.mixin"

    transaction_id = fields.Integer(
        'Transaction ID'
    )
    transaction_model_name = fields.Char(
        'Transaction Model Name'
    )
    transaction_ref = fields.Reference(
        string='Transaction Ref',
        selection="_selection_transaction_models",
        compute='_compute_transaction_ref',
        inverse='_inverse_transaction_ref',
        store=False,
        copy=False
    )
    def get_transaction_object(self):
        if not self.transaction_model_name:
            return False
        if not self.transaction_id :
            return self.env[self.transaction_model_name].browse()
        """Get the parent document ID if available."""
        # This method should be overridden in child classes if needed
        return self.env[self.transaction_model_name].browse(self.transaction_id)

    @api.model
    def _selection_transaction_models(self):
        """
        Mengambil model yang valid untuk dijadikan referensi.
        Bisa disaring sesuai kebutuhan (misal hanya model dengan field 'name').
        """
        models = self.env['ir.model'].search([('transient', '=', False)])
        # Filter hanya model yang punya field 'name'
        valid_models = []
        for m in models:
            try:
                valid_models.append((m.model, m.name))
            except:
                continue

        return valid_models

    @api.depends('transaction_model_name', 'transaction_id')
    def _compute_transaction_ref(self):
        env = self.env
        """Hitung field Reference dari model name dan ID"""
        for record in self:
            model = record.transaction_model_name
            res_id = record.transaction_id
            if model and model in env and res_id:
                record_ok = env[model].browse(res_id).exists()
                if record_ok:
                    record.transaction_ref = f"{model},{res_id}"
            else:
                record.transaction_ref = False

    def _inverse_transaction_ref(self):
        """Ketika user mengubah Reference, isi ulang model name & ID"""
        for record in self:
            if record.transaction_ref:
                record.transaction_model_name = record.transaction_ref._name
                record.transaction_id = record.transaction_ref.id
            else:
                record.transaction_model_name = False
                record.transaction_id = False

    def action_approval_transaction(self):
        if self.transaction_model_name and self.transaction_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Transaction',
                'res_model': self.transaction_model_name,
                'res_id': self.transaction_id,
                'view_mode': 'form',
                'context': {
                    'create': 0,
                    'edit': 0,
                    'delete': 0
                }
            }
        else:
            raise UserError("No Transaction")
