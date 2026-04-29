# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class purchase_request_wizard(models.TransientModel):
    _name = 'purchase.request.wizard'
    _description = 'Purchase Request Wizard'


    line_ids = fields.One2many(
        'purchase.request.wizard.line', 'request_wizard_id')
    origin = fields.Char('Origin')
    picking_id = fields.Many2one('stock.picking')


    def action_request_purchase(self):
        purchase_request_obj = self.env['purchase.request']
        purchase_request_line_obj = self.env['purchase.request.line']
        purchase_request_id = False
        for line_id in self.line_ids:
            purchase_request_id = purchase_request_obj.search(
                [('product_id', '=', line_id.product_id.id),('state','=','requested')])
            if purchase_request_id:
                purchase_request_id.request_quantity += line_id.request_quantity
                purchase_request_id.purchase_qty += line_id.request_quantity

                purchase_request_line_id = purchase_request_line_obj.search(
                    [('origin', '=', self.origin or self.picking_id.name),
                    ('purchase_request_id','=',purchase_request_id.id)])
                if purchase_request_line_id:
                    raise Warning('Material has been requested!')
                else:
                    purchase_request_id.line_ids = [(0,0,{
                        'origin' : self.picking_id.origin or self.picking_id.name,
                        'request_quantity' : line_id.request_quantity,
                    })]
            else:
                purchase_request_id = purchase_request_obj.create({
                    'product_id' : line_id.product_id.id,
                    'request_quantity' : line_id.request_quantity,
                    'purchase_qty' : line_id.request_quantity,
                    'line_ids' : [(0,0,{
                        'origin' : self.picking_id.origin or self.picking_id.name,
                        'request_quantity' : line_id.request_quantity,
                    })],
                })
            
        if purchase_request_id:
            return {
                'name': _('Material Request'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'request.info',
                'target': 'new',
                'context': {'default_text':'Requested'},
            }

class purchase_request_wizard_line(models.TransientModel):
    _name = 'purchase.request.wizard.line'
    _description = 'Purchase Request Wizard Line'


    product_id = fields.Many2one('product.product', 'Product')
    request_quantity = fields.Float('Request Quantity')
    request_wizard_id = fields.Many2one(
        'purchase.purchase.wizard', 'Request Wizard')
    product_uom = fields.Many2one('product.uom', 'UoM')