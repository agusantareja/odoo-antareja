# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class metalindo_stock_picking(models.Model):
    _inherit = 'stock.picking'


    purchase_id = fields.Many2one('purchase.order', string="Purchase Orders")
    purchase_request_id = fields.Many2one('purchase.request')


    def button_validate(self):
        res = super(metalindo_stock_picking, self).button_validate()
        # import web_pdb; web_pdb.set_trace()
        for rec in self:
            if rec.purchase_id:
                if rec.location_dest_id.usage == 'internal':
                    rec.purchase_id.picking_state = 'received'
                else:
                    rec.purchase_id.picking_state = 'transit'
        return res

    def request_purchase(self):
        context = self.env.context.copy()
        origin = self.origin
        context.update({
            'default_picking_id' : self.id,
            'default_origin': origin,
            'default_line_ids': [(0, 0, {
                'product_id': x.product_id.id,
                'request_quantity' : x.product_uom_qty,
                'product_uom' : x.product_uom.id,
            }) for x in self.move_ids_without_package]
        })
        return {
            'name': _('Material Request'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.request.wizard',
            'target': 'new',
            'context': context,
        }
