# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class MetalindoStockOrderPoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'


    product_min_qty = fields.Float(string="Reordering Point")
    product_max_qty = fields.Float(string="Reordering Quantity")


    def get_reserved_qty(self):
        reserved_qty = 0
        query = """
        select sum(reserved_quantity) from stock_quant
        where product_id = %s
        and location_id = %s
        """%(self.product_id.id,self.location_id.id)
        self.env.cr.execute(query)
        res = self.env.cr.fetchone()
        if res:
            reserved_qty = res[0]
        return reserved_qty

    @api.model
    def get_recommend_qty(self,ROP,ROQ,SOH, BRO, PO_ONGOING):
        setting_id = self.env.ref('metalindo_purchase.recommend_qty_setting_id')
        recommend_qty_code = setting_id.code
        recommend_qty = eval(recommend_qty_code)
        return recommend_qty

    @api.constrains('product_min_qty','product_max_qty','product_id','company_id')
    def update_recommend_qty(self):
        recommend_qty_obj = self.env['recommend.qty']
        for rec in self:
            # hanya buat recommend qty jika min > 0 dan max > 0
            if not (rec.product_min_qty > 0.0 and rec.product_max_qty > 0.0):
                continue
            qty_available = rec.product_id.qty_available
            if qty_available <= rec.product_min_qty:
                bro_records = self.env['recommend.qty'].search([
                    ('product_id', '=', rec.product_id.id),
                    ('company_id', '=', self.env.company.id),
                    ('bro_purchase_qty','>',0),
                    ('state', 'not in', ['Draft', 'Done'])])
                bro_ref_number = ', '.join(bro_records.mapped('name'))
                bro_qty = sum(
                    bro_records.mapped(
                        lambda r: r.outstanding_qty if r.state in ['Assignment', 'Ready to Purchase'] else max(r.bro_purchase_qty - r.real_purchase_order_qty, 0)
                    )
                )
                po_line_ongoing = self.env['purchase.order.line'].search([('order_id.is_rfq_tender', '=', False),('state', '!=', 'cancel'),('product_id', '=', rec.product_id.id), ('company_id','=',rec.company_id.id)])
                po_line_ongoing_qty = 0
                po_ids = []
                for po_line in po_line_ongoing:
                    if po_line.product_qty > po_line.qty_received:
                        po_line_ongoing_qty += po_line.product_qty - po_line.qty_received
                        po_ids.append(po_line.order_id.name)
                
                po_ref_number = ', '.join(po_ids)

                recommend_qty = rec.get_recommend_qty(rec.product_min_qty,rec.product_max_qty,qty_available, bro_qty, po_line_ongoing_qty)
                vals = {
                    'product_id' : rec.product_id.id,
                    'product_min_qty' : rec.product_min_qty,
                    'product_max_qty' : rec.product_max_qty,
                    'bro_qty': bro_qty,
                    'bro_ref_number': bro_ref_number,
                    'po_ref_number': po_ref_number,
                    'po_qty': po_line_ongoing_qty,
                    'company_id' : rec.company_id.id,
                    'qty_available' : qty_available,
                    'recommend_date' : datetime.now(),
                    'recommend_qty' : recommend_qty,
                    'orderpoint_id' : rec.id,
                    'purchase_qty' : recommend_qty,
                    'reserved_qty' : rec.get_reserved_qty(),
                }
                recommend_qty_id = recommend_qty_obj.search([('product_id','=',rec.product_id.id),('company_id','=',rec.company_id.id)],limit=1)
                if recommend_qty_id and recommend_qty_id.state == 'Draft':
                    recommend_qty_id.write(vals)
                else:
                    recommend_qty_obj.create(vals)
