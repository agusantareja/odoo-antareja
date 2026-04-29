# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MetalindoStockMove(models.Model):
    _inherit = 'stock.move'


    # item_no = fields.Integer(string='PO Item Number', related='purchase_line_id.item_no')
    mir_line_id = fields.Many2one('material.inventory.request.line', string='Material Issue Request Line')
    description = fields.Text(compute='_compute_description', store=True)
    manufacturer_id = fields.Many2one(comodel_name='res.partner', compute='_compute_description', store=True)
    part_number = fields.Char(compute='_compute_description', store=True)

    @api.constrains('purchase_line_id','mir_line_id')
    def get_ref(self):
        for rec in self:
            if rec.purchase_line_id:
                rec.origin = rec.purchase_line_id.order_id.name + '-' + str(rec.purchase_line_id.item_no)
            elif rec.mir_line_id:
                rec.origin = rec.mir_line_id.request_id.name + '-' + str(rec.mir_line_id.item_no)

    @api.depends('purchase_line_id', 'product_id')
    def _compute_description(self):
        for rec in self:
            if rec.purchase_line_id:
                rec.description = rec.purchase_line_id.description.strip() if rec.purchase_line_id.description else rec.purchase_line_id.description
                if rec.purchase_line_id.remarks:
                    rec.description += f'\n\nREMARKS:\n{rec.purchase_line_id.remarks.strip()}'
                rec.manufacturer_id = rec.purchase_line_id.manufacturer_id
                rec.part_number = rec.purchase_line_id.part_number
            else:
                rec.description = rec.product_id.description.strip() if rec.product_id.description else rec.product_id.description
                rec.manufacturer_id = rec.product_id.manufacturer_id
                rec.part_number = rec.product_id.part_number

    @api.constrains('state')
    def check_recommend_qty(self):
        orderpoint_obj = self.env['stock.warehouse.orderpoint'].sudo()
        for rec in self:
            if rec.state == 'done' and rec.product_id.detailed_type == 'product' and rec.location_dest_id.usage == 'customer':
                orderpoint_id = orderpoint_obj.search([('company_id','=',rec.company_id.id),('product_id','=',rec.product_id.id)])
                if orderpoint_id:
                    orderpoint_id.update_recommend_qty()
            if rec.state == 'done' and rec.purchase_line_id and rec.picking_type_id == rec.purchase_line_id.order_id.picking_type_id:
                rec.purchase_line_id.write_received()
