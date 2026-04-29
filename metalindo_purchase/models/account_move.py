# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMoveMetalindo(models.Model):
    _inherit = 'account.move'

    ref_file = fields.Binary(string='Reference File (pdf)', attachment=True)


    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res.attachment_from_po()
        return res
    
    def write(self, vals):
        res = super().write(vals)
        self.attachment_from_po()
        return res
    
    def attachment_from_po(self):
        for amv in self.filtered(lambda m: m.move_type == 'in_invoice'):
            orders = amv.invoice_line_ids.purchase_line_id.order_id
            if not orders:
                continue

            existing_names = set(amv.attachment_ids.mapped('name'))
            po_attachments = self.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'purchase.order'),
                ('res_id', 'in', orders.ids),
                ('name', 'not in', list(existing_names)),
            ])
            for att in po_attachments:
                if att.name in existing_names:
                    continue
                att.copy({
                    'res_model': 'account.move',
                    'res_id': amv.id,
                })

class AccountMoveLineMetalindo(models.Model):
    _inherit = 'account.move.line'

    purchase_category_id = fields.Many2one('purchase.category', 'Purchase Category')
    hs_code = fields.Char('HS Code')
    # invoice_payment_state = fields.Selection(string='Payment', related='move_id.invoice_payment_state', store=True)
    state = fields.Selection(string='State', related='move_id.state', store=True)
    invoice_type = fields.Selection(string='Type', related='move_id.move_type', store=True)
    impor_domestik = fields.Selection(string='Impor/Domestik', related='move_id.partner_id.code_id.impor_domestik', store=True)
    # price_unit_idr = fields.Integer('Unit Price (IDR)', compute='_compute_price')
    # price_unit_usd = fields.Integer('Unit Price (USD)', compute='_compute_price')
    # price_subtotal_idr = fields.Integer('Price Subtotal (IDR)', compute='_compute_price')
    # price_subtotal_usd = fields.Integer('Price Subtotal (USD)', compute='_compute_price')
    # belanja_tkdn_idr = fields.Integer('Belanja TKDN (IDR)', compute='_compute_price')
    # kab_kota = fields.Char(string='Kab/Kota Asal Belanja', compute='_compute_purchase_category')
    # provinsi = fields.Char(string='Provinsi Asal Belanja', related='move_id.partner_id.state_id.name')
    # negara = fields.Char(string='Negara Asal Belanja', related='move_id.partner_id.country_id.name')
    # area_project = fields.Char(string='Area Project', compute='_compute_purchase_category')
    # tkdn_sa = fields.Float(string='TKDN SA', compute='_compute_purchase_category')
    # tkdn_s = fields.Float(string='TKDN S', compute='_compute_purchase_category')
    # usd_id = fields.Many2one('res.currency', 'USD', compute='_compute_purchase_category')
    # idr_id = fields.Many2one('res.currency', 'IDR', compute='_compute_purchase_category')
    # jenis_barang = fields.Char(string='Jenis Barang', compute='_compute_purchase_category')
    # kode_hs = fields.Char(string='Kode HS', compute='_compute_purchase_category')
    # spec = fields.Char('Spesifikasi', compute='_compute_purchase_category')
    # purchase_plan_id = fields.Many2one('purchase.plan', compute='_compute_purchase_plan', store=True)

    @api.onchange('product_id')
    def _onchange_product_id_purchase_category_id(self):
        self.purchase_category_id = self.product_id.product_tmpl_id.purchase_category_id
        self.hs_code = self.product_id.product_tmpl_id.hs_code

    def unlink(self):
        attachments = self.env['ir.attachment'].sudo()
        for line in self.filtered(lambda l: l.purchase_line_id.order_id.name and l.move_id.id):
            attachments |= attachments.search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', line.move_id.id),
                ('name', 'ilike', line.purchase_line_id.order_id.name),
            ])
        attachments.unlink()
        return super().unlink()
    
    # @api.depends('purchase_category_id', 'move_id.date')
    # def _compute_purchase_plan(self):
    #     # import web_pdb; web_pdb.set_trace()
    #     for rec in self:
    #         if rec.purchase_category_id and rec.move_id.date:
    #             plan_ids = rec.purchase_category_id.plan_ids.filtered(lambda x: x.tahun == str(rec.move_id.date.year))
    #             if len(plan_ids) > 0:
    #                 rec.purchase_plan_id = plan_ids[0]
    #             else:
    #                 rec.purchase_plan_id = None
    #         else:
    #             rec.purchase_plan_id = None

    # def _compute_purchase_category(self):
    #     for rec in self:
    #         rec.kab_kota = rec.move_id.partner_id.city or rec.move_id.partner_id.code_id.name
    #         rec.area_project = 'Lapaopao RKEF Smelter FeNi Project'
    #         rec.tkdn_sa = 0.0
    #         rec.tkdn_s = 0.0
    #         rec.usd_id = self.env.ref('base.USD')
    #         rec.idr_id = self.env.ref('base.IDR')
    #         if rec.move_id.partner_id.tkdn == 'self_assessment':
    #             rec.tkdn_sa = rec.move_id.partner_id.tkdn_persen
    #         if rec.move_id.partner_id.tkdn == 'certificate':
    #             rec.tkdn_s = rec.move_id.partner_id.tkdn_persen
    #         rec.jenis_barang = rec.product_id.name or rec.name
    #         rec.kode_hs = rec.product_id.product_tmpl_id.hs_code or rec.hs_code
    #         if rec.product_id:
    #             if rec.product_id.product_tmpl_id.description:
    #                 rec.spec = rec.product_id.product_tmpl_id.description
    #             else:
    #                 rec.spec = rec.product_id.name
    #         else:
    #             rec.spec = rec.name

    # def _compute_price(self):
    #     # import web_pdb; web_pdb.set_trace()
    #     idr_id = self.env.ref('base.IDR')
    #     usd_id = self.env.ref('base.USD')
    #     for rec in self:
    #         if rec.currency_id.rate > 0.0:
    #             if rec.currency_id == idr_id:
    #                 rec.price_unit_idr = round(rec.price_unit)
    #                 rec.price_subtotal_idr = round(rec.price_subtotal)
    #             else:
    #                 rec.price_unit_idr = round((idr_id.rate / rec.currency_id.rate) * rec.price_unit)
    #                 rec.price_subtotal_idr = round((idr_id.rate / rec.currency_id.rate) * rec.price_subtotal)
    #             if rec.currency_id == usd_id:
    #                 rec.price_unit_usd = round(rec.price_unit)
    #                 rec.price_subtotal_usd = round(rec.price_subtotal)
    #             else:
    #                 rec.price_unit_usd = round((usd_id.rate / rec.currency_id.rate) * rec.price_unit)
    #                 rec.price_subtotal_usd = round((usd_id.rate / rec.currency_id.rate) * rec.price_subtotal)
    #         else:
    #             rec.price_unit_idr = round(rec.price_unit)
    #             rec.price_unit_usd = round(rec.price_unit)
    #             rec.price_subtotal_idr = round(rec.price_subtotal)
    #             rec.price_subtotal_usd = round(rec.price_subtotal)
    #         rec.belanja_tkdn_idr = round(rec.price_subtotal_idr * rec.move_id.partner_id.tkdn_persen)
