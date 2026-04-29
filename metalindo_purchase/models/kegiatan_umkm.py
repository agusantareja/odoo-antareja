from odoo import api, fields, models, _


class KegiatanUMKM(models.Model):
    _name = 'kegiatan.umkm'
    _description = 'Jenis Komitmen pada UMKM'

    name = fields.Char('Nama Kegiatan')
    purchase_ids = fields.One2many('purchase.order.line', 'umkm_id', 'Purchase')
    purchase_count = fields.Integer(string='Purchase Count', compute='_compute_purchase')
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency')
    purchase_value = fields.Monetary('Purchase Value', currency_field='currency_id', compute='_compute_purchase')
    vendor = fields.Text(string='Vendor', compute='_compute_vendor', search='_search_vendor', store=False)

    def _compute_vendor(self):
        for record in self:
            desc = []
            for line in record.purchase_ids.filtered(lambda r: r.state in ('purchase', 'done')):
                if line.order_id.partner_id.name not in desc:
                    desc.append(line.order_id.partner_id.name)
            if desc:
                vendor = '\n'.join(desc)
            else:
                vendor = None
            record.vendor = vendor

    def _search_vendor(self, operator, value):
        ids = []
        res = self.env['res.partner'].search([
            ('name', 'ilike', value), 
            ('code_id.code', '=', 'UMKM')
            ])
        if res:
            vendor_ids = [x.id for x in res]
            order_ids = self.env['purchase.order.line'].search([
                ('partner_id', 'in', vendor_ids),
                ('state', 'in', ['purchase', 'done'])
                ])
            for line in order_ids:
                if line.umkm_id.id not in ids:
                    ids.append(line.umkm_id.id)
        return [('id', 'in', ids)]

    def _compute_currency(self):
        for rec in self:
            rec.currency_id = self.env.company.currency_id

    def _compute_purchase(self):
        for rec in self:
            count = 0
            value = 0
            for po in rec.purchase_ids.filtered(lambda r: r.state in ('purchase', 'done')):
                count += 1
                value += (rec.currency_id.rate / po.order_id.currency_id.rate) * po.price_subtotal
            rec.purchase_count = count
            rec.purchase_value = value

    def action_show_purchase(self):
        self.ensure_one()
        # Jika ingin memberi judul/name action, mesti disebut full begini, tidak bisa hanya modifikasi action XML
        tree_id = self.env.ref('metalindo_purchase.kegiatan_umkm_purchase_order_line_tree').id
        form_id = self.env.ref('purchase.purchase_order_line_form2').id
        action = {
            'type': 'ir.actions.act_window', 
            'name': self.name + ' / Purchase Order Line',
            'res_model': 'purchase.order.line',
            'view_mode': 'tree,form',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'search_view_id': self.env.ref('purchase.purchase_order_line_search').id,
            'domain': [('umkm_id', '=', self.id)],
            }
        return action