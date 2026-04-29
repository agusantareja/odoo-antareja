# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import ast
import logging


_logger = logging.getLogger(__name__)


class CniMaterialRequisition(models.Model):
    _inherit = 'material.requisition.line'

    def write(self, values):
        product_type = self.env['pr.product.type']
        uom_uom = self.env['uom.uom']

        for line in self:

            # Ambil nilai baru dengan fallback ke nilai lama
            new_qty = values.get('qty', line.qty)
            new_pr_product_type_id = values.get('pr_product_type_id', line.pr_product_type_id.id)
            new_uom_id = values.get('uom_id', line.uom_id.id)
            new_priority = values.get('priority', line.priority)
            new_reason = values.get('reason', line.reason)
            new_notes = values.get('notes', line.notes)

            # Cek jika tidak ada perubahan signifikan
            if (
                new_qty == line.qty and
                new_pr_product_type_id == line.pr_product_type_id.id and
                new_priority == line.priority and
                new_reason == line.reason and
                new_uom_id == line.uom_id.id
            ):
                continue
            
            message_values = {
                'no': line.no,
                'product_display_name': line.product_id.display_name,
                'priority': line.priority,
                'reason': line.reason,
                'qty': line.qty,
                'qty_new': new_qty,
                'priority_new': new_priority,
                'reason_new': new_reason,
                'product_type_display_name': line.pr_product_type_id.display_name,
                'product_type_display_name_new': product_type.browse(new_pr_product_type_id).display_name,
                'uom_display_name': line.uom_id.display_name,
                'uom_display_name_new': uom_uom.browse(new_uom_id).display_name,
                'notes': new_notes,
            }

            _logger.info(message_values)

            line.mr_id.message_post_with_view(
                'metalindo_direct_charge_approval.track_purchase_request_line',
                values=message_values,
                subtype_id=self.env.ref('mail.mt_note').id
            )

        return super(CniMaterialRequisition, self).write(values)
