# -*- coding: utf-8 -*-

import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class product_template(models.Model):
    _inherit = 'product.template'

    purchase_category_id = fields.Many2one('purchase.category', 'Purchase Category', tracking=1)
    sro_qty = fields.Float(compute='compute_qty_bro')
    bro_qty = fields.Float(compute='compute_qty_bro')
    po_incoming_qty = fields.Float(compute='compute_qty_bro', string='Incoming Qty')

    # def _compute_purchase_line_ids(self):
    #     po_line_obj = self.env['purchase.order.line']
    #     for template in self:
    #         all_part_numbers = self.product_part_number_ids.mapped('name')
    #         purchase_lines = po_line_obj.search([
    #             ('part_number', 'in', all_part_numbers),
    #             ('state', 'in', ['done', 'purchase']),
    #         ], order='date_planned desc, id desc') if all_part_numbers else po_line_obj.browse([])
    #         latest_purchase_line = purchase_lines[:1]

    #         template.purchase_line_ids = purchase_lines

    #         if latest_purchase_line:
    #             template.last_purchase = latest_purchase_line.order_id.name
    #             template.last_purchase_price = latest_purchase_line.price_unit
    #             template.last_purchase_uom_id = latest_purchase_line.product_uom
    #             template.last_purchase_currency_id = latest_purchase_line.currency_id
    #         else:
    #             template.last_purchase = False
    #             template.last_purchase_price = False
    #             template.last_purchase_uom_id = False
    #             template.last_purchase_currency_id = False

    def compute_qty_bro(self):
        for this in self:
            sro_qty = self.env['recommend.qty'].search([
                ('product_id.product_tmpl_id', '=', this.id),
                ('company_id', '=', self.env.company.id),
                ('purchase_qty','>',0),
                ('state', '=', 'Draft')]).mapped('purchase_qty')
            bro_records = self.env['recommend.qty'].search([
                ('product_id.product_tmpl_id', '=', this.id),
                ('company_id', '=', self.env.company.id),
                ('bro_purchase_qty','>',0),
                ('state', 'not in', ['Draft', 'Done'])])
            bro_qty = bro_records.mapped(
                lambda r: r.outstanding_qty if r.state in ['Assignment', 'Ready to Purchase'] else max(r.bro_purchase_qty - r.real_purchase_order_qty, 0)
            )
            po_line_ongoing =  self.env['purchase.order.line'].search([('order_id.is_rfq_tender', '=', False), ('state', '!=', 'cancel'),('product_id.product_tmpl_id', '=', this.id), ('company_id','=',self.env.company.id)])
            po_line_ongoing_qty = 0
            for po_line in po_line_ongoing:
                if po_line.product_qty > po_line.qty_received:
                    po_line_ongoing_qty += po_line.product_qty - po_line.qty_received

            this.sro_qty = sum(sro_qty)
            this.bro_qty = sum(bro_qty)
            this.po_incoming_qty = po_line_ongoing_qty

    def action_view_sro(self):
        recommend_qty_ids = self.env['recommend.qty'].search([('product_id.product_tmpl_id', '=', self.id)]).ids
        domain = [('id', 'in', recommend_qty_ids),('purchase_qty','>',0),('state', '=', 'Draft')]
        action = self.env["ir.actions.actions"]._for_xml_id("metalindo_purchase.report_recommended_quantity_inventory_action")
        action['domain'] = domain
        action['context'] = {'create': 0, 'edit': 0, 'copy': 0, 'delete': 0}
        return action
    
    def action_view_bro(self):
        bro_records = self.env['recommend.qty'].search([
            ('product_id.product_tmpl_id', '=', self.id),
            ('company_id', '=', self.env.company.id),
            ('bro_purchase_qty','>',0),
            '|',
            ('state', 'in', ['Assignment', 'Ready to Purchase', 'On Tender']),
            '&',
            ('state', '=', 'In Procurement'),
            ('purchase_ids', '!=', False),
        ])
        domain = [('id', 'in', bro_records.ids)]
        view_pair_tree = (self.env.ref('metalindo_purchase.report_recommended_quantity_purchase_tree').id,'tree')
        search_view_id = self.env.ref('metalindo_purchase.report_recommended_quantity_purchase_search').id
        views = [view_pair_tree]
        action = {
            'type': 'ir.actions.act_window',
            'name': 'BRO',
            'res_model': 'recommend.qty',
            'view_mode': 'tree',
            'views': views,
            'search_view_id': search_view_id,
            'context': {'create': 0, 'edit': 0, 'copy': 0, 'delete': 0},
            'domain': domain,
        }
        return action
    
    def action_view_po_incoming(self):
        po_line_ids = []
        po_line_ongoing =  self.env['purchase.order.line'].search([('state', '!=', 'cancel'),('product_id.product_tmpl_id', '=', self.id), ('company_id','=',self.env.company.id)])
        for po_line in po_line_ongoing:
            if po_line.product_qty > po_line.qty_received:
                po_line_ids.append(po_line.id)
        domain = [('id', 'in', po_line_ids)]

        action = self.env["ir.actions.actions"]._for_xml_id("metalindo_purchase.action_purchase_incoming")
        action['domain'] = domain
        action['display_name'] = _("Purchase Incoming for %s", self.display_name)
        return action
    
    def action_view_stock_move(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_action")
        action['domain'] = [('product_id.product_tmpl_id', 'in', self.ids)]
        return action
