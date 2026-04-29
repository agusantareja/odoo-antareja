# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.float_utils import float_compare
import logging
_logger = logging.getLogger(__name__)


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    discount = fields.Float('Discount')

    def check_gr_done(self, original_self):
        for line in original_self:
            move_states = self.env['stock.move'].sudo().search([
                ('purchase_line_id', '=', line.id)
            ]).mapped('state')

            if 'done' in move_states:
                raise ValidationError(_(
                    'Revisions are not allowed because the item "%s" has already been received.'
                ) % line.product_id.display_name)

    def write(self, vals):
        if not vals.get('item_no', 'source'):
            for line in self:
                # Ambil move yang terkait line ini
                move_states = self.env['stock.move'].sudo().search([
                    ('purchase_line_id', '=', line.id),
                    ('picking_id.picking_type_id', '=', line.order_id.picking_type_id.id)
                ]).mapped('state')

                # Cek apakah sudah done
                if 'done' in move_states:
                    # Cek apakah data berubah
                    for field, new_value in vals.items():
                        if field in line:
                            old_value = line[field]
                            # Bandingkan nilai lama dan baru
                            if isinstance(old_value, models.BaseModel):  # untuk field Many2one
                                old_value = old_value.id
                            if old_value != new_value:
                                raise ValidationError(_(
                                    'You cannot revise line "%s" because it has already been received (GR done).'
                                ) % line.product_id.display_name)
                            
        return super().write(vals)

    def unlink(self):
        for line in self:
            move_states = self.env['stock.move'].sudo().search([
                ('purchase_line_id', '=', line.id),
                ('picking_id.picking_type_id', '=', line.order_id.picking_type_id.id)
            ]).mapped('state')

            if 'done' in move_states:
                raise ValidationError(_(
                    'You cannot delete line "%s" because it has already been received (GR done).'
                ) % line.product_id.display_name)
        
        return super().unlink()
    
    def _get_outgoing_incoming_moves(self):
        outgoing_moves = self.env['stock.move']
        incoming_moves = self.env['stock.move']

        # for move in self.move_ids.filtered(lambda r: r.state != 'cancel' and not r.scrapped and self.product_id == r.product_id):original code
        for move in self.move_ids.filtered(lambda r: r.state != 'cancel'\
            and not r.scrapped \
            and self.product_id == r.product_id\
            and r.picking_id.picking_type_id == self.order_id.picking_type_id):
            if move._is_purchase_return() and move.to_refund:
                outgoing_moves |= move
            elif move.location_dest_id.usage != "supplier":
                if not move.origin_returned_move_id or (move.origin_returned_move_id and move.to_refund):
                    incoming_moves |= move

        return outgoing_moves, incoming_moves
