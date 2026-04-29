# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class purchase_request(models.Model):
    _inherit = 'recommend.qty'
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', 'Product')
    line_ids = fields.One2many('purchase.request.line','purchase_request_id', string='Request')
    request_quantity = fields.Float('Request Quantity')
    purchase_qty = fields.Float('Quantity to Purchase')
    company_id = fields.Many2one(
        'res.company', default=lambda x: x.env.company.id)
    product_uom = fields.Many2one('product.uom', 'UoM')
    requester = fields.Many2many('metalindo.analytic',string="Cost Center",compute="get_cost_center")

    def get_cost_center(self):
        for rec in self:
            rec.requester = rec.line_ids.mapped('analytic_id')


class purchase_request_line(models.Model):
    _name = 'purchase.request.line'
    _description = 'Purchase Request Line'

    origin = fields.Char('Origin')
    request_quantity = fields.Float('Quantity')
    purchase_request_id = fields.Many2one('purchase.request')
    analytic_id = fields.Many2one('metalindo.analytic','Cost Center')


class request_info(models.TransientModel):
    _name = 'request.info'
    _description = 'Request Info'

    text = fields.Text()
