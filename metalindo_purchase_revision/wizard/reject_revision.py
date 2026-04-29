# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class RejectRevision(models.TransientModel):
    _name = 'reject.revision'
    _description = 'Reject Revision'

    reason = fields.Text('Reason')
    purchase_id = fields.Many2one('purchase.order')

    def button_save(self):
        self.purchase_id.write({
            'state': 'purchase',
            'revision_reason': self.purchase_id.previous_revision_reason,
            'previous_revision_reason': False,
        })
        # Buat picking baru untuk mengganti yang dibatalkan
        move = self.env['stock.move'].sudo().search([
            ('purchase_line_id', 'in', [l.id for l in self.purchase_id.order_line]),
            ('state', '=', 'cancel'),
        ], order='id desc', limit=1)
        if move:
            picking = move.picking_id.copy()
            picking.action_assign()
        self.purchase_id.message_post(body="Reject PO Revision Request, Reason: %s"%self.reason)
        return True
