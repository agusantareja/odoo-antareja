from odoo import api, fields, models, _


class material_discrepancy(models.Model):
    _name = 'material.discrepancy'
    _description = 'Material Disrepancy Report'
    _rec_name = 'purchase_line_id'

    purchase_line_id = fields.Many2one('purchase.order.line')
    purchase_id = fields.Many2one('purchase.order', 'Purchase Order', related='purchase_line_id.order_id', store=True)
    product_id = fields.Many2one('product.product', related='purchase_line_id.product_id')
    qty_order = fields.Float('Qty Order', related='purchase_line_id.product_qty')
    qty_receive = fields.Float('Qty Receive', related='purchase_line_id.qty_received')
    product_uom_category_id = fields.Many2one('uom.category', related='purchase_line_id.product_uom_category_id')
    product_uom = fields.Many2one('uom.uom', 'UoM', related='purchase_line_id.product_uom')
    backorder_status = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Backorder', tracking=True)
    discrepancy_note = fields.Text('MDR Note', copy=False, tracking=True)
    receiving_discrepancy_note = fields.Text('Receiving Note', compute='_compute_receiving_discrepancy_note')
    move_ids = fields.One2many('stock.move', 'purchase_line_id', related='purchase_line_id.move_ids')

    def _compute_receiving_discrepancy_note(self):
        for rec in self:
            note = [move.discrepancy_note for move in rec.purchase_line_id.move_ids.filtered(lambda x: x.discrepancy_note)]
            rec.receiving_discrepancy_note = False if not note else '\n'.join(note)

