# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class purchase_category(models.Model):
    _name = 'purchase.category'
    _order = 'name'
    _description = "Purchase Category"

    name = fields.Char('Kategori')
    plan_ids = fields.One2many('purchase.plan', 'category_id', 'Rencana')
    real_ids = fields.One2many('account.move.line', 'purchase_category_id', 'Realisasi')
    urutan = fields.Integer('Urutan', default=0)


class purchase_plan_year(models.Model):
    _name = 'purchase.plan.year'
    _description = 'Grouping Purchase Plan by Year'

    def _selection_tahun(self):
        # import web_pdb; web_pdb.set_trace()
        total_id = self.env.ref('metalindo_purchase.purchase_category_total')
        year_ids = list(set(self.env['purchase.plan'].sudo().search([
            # ('category_id', '=', total_id.id)
            ], order='year_id').mapped('year_id')))
        list_tahun = self.env['purchase.plan.year'].sudo().search([
            ('id', 'in', [x.id for x in year_ids])
            ], order='name').mapped('name')
        tahun = False
        if len(list_tahun) > 0:
            tahun = list_tahun[0]
        if not tahun:
            tahun = fields.Date.context_today(self).strftime('%Y')
        select_tahun = []
        for n in range(len(list_tahun)+3):
            str_tahun = str(int(tahun) + n)
            select_tahun.append((str_tahun, str_tahun))
        return select_tahun

    name = fields.Selection(selection=lambda self:self._selection_tahun(), string='Tahun')
    plan_ids = fields.One2many('purchase.plan', 'year_id', 'Rencana Belanja')
    usd_id = fields.Many2one('res.currency', 'USD', compute='_compute_currency')
    idr_id = fields.Many2one('res.currency', 'IDR', compute='_compute_currency')
    real_impor_usd = fields.Float('Total Realisasi Impor (USD)', compute='_compute_purchase')
    real_domestik_idr = fields.Float('Total Realisasi Domestik (IDR)', compute='_compute_purchase')
    real_belanja_tkdn = fields.Float('Total Realisasi Belanja TKDN (IDR)', compute='_compute_purchase')
    sum_impor_usd = fields.Float('Total Impor (USD)', compute='_compute_purchase')
    sum_domestik_idr = fields.Float('Total Domestik (IDR)', compute='_compute_purchase')
    sum_belanja_tkdn = fields.Float('Total Belanja TKDN (IDR)', compute='_compute_purchase')
    persen_real_impor_usd = fields.Float('Persentase Realisasi Impor (%)', compute='_compute_purchase')
    persen_real_domestik_idr = fields.Float('Persentase Realisasi Domestik (%)', compute='_compute_purchase')
    persen_real_belanja_tkdn = fields.Float('Persentase Realisasi Belanja TKDN (%)', compute='_compute_purchase')
    persen_sum_impor_usd = fields.Float('Persentase Impor (%)', compute='_compute_purchase')
    persen_sum_domestik_idr = fields.Float('Persentase Domestik (%)', compute='_compute_purchase')
    persen_sum_belanja_tkdn = fields.Float('Persentase Belanja TKDN (%)', compute='_compute_purchase')
    capaian_real_impor_usd = fields.Float('Capaian Realisasi Impor (%)', compute='_compute_purchase')
    capaian_real_domestik_idr = fields.Float('Capaian Realisasi Domestik (%)', compute='_compute_purchase')
    capaian_real_belanja_tkdn = fields.Float('Capaian Realisasi Belanja TKDN (%)', compute='_compute_purchase')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)

    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Tidak boleh ada tahun yang sama!'),
        ]

    # Untuk button "Realisasi" di tree view, tapi gak jadi
    def action_show_realisasi(self):
        self.ensure_one()
        action = self.env.ref('metalindo_purchase.realisasi_belanja_action').read()[0]
        action['domain'] = [('year_id', '=', self.id)]
        action['context'] = {'create': 0, 'edit': 0, 'delete': 0}
        return action

    @api.model_create_multi
    def create(self, vals_list):
        # import web_pdb; web_pdb.set_trace()
        res = super(purchase_plan_year, self).create(vals_list)
        # Tambahkan semua kategori
        lines = []
        for cat_id in self.env['purchase.category'].search([]):
            lines.append((0, 0, {
                'category_id': cat_id.id,
                'year_id': res.id,
                'company_id': res.company_id.id,
                }))
        res.plan_ids = lines
        return res

    def _compute_currency(self):
        for rec in self:
            rec.usd_id = self.env.ref('base.USD')
            rec.idr_id = self.env.ref('base.IDR')

    def _compute_purchase(self):
        # import web_pdb; web_pdb.set_trace()
        for rec in self:
            # plan
            ids = self.env['purchase.plan'].search([('tahun', '=', rec.name)])
            sum_impor_usd = sum(ids.mapped('impor_usd')) or 0.0
            sum_domestik_idr = sum(ids.mapped('domestik_idr')) or 0.0
            sum_belanja_tkdn = sum(ids.mapped('belanja_tkdn')) or 0.0
            # realisasi
            ids = self.env['view.realisasi.belanja'].search([('tahun', '=', rec.name)])
            real_impor_usd = sum(ids.filtered(lambda x: x.impor_domestik == 'impor').mapped('price_subtotal_usd')) or 0.0
            domestik = ids.filtered(lambda x: x.impor_domestik == 'domestik')
            real_domestik_idr = sum(domestik.mapped('price_subtotal_idr')) or 0.0
            real_belanja_tkdn = sum(
                [line.price_subtotal_idr * line.aml_id.move_id.partner_id.tkdn_persen for line in domestik]
                ) or 0.0
            # total
            rec.sum_impor_usd = sum_impor_usd
            rec.sum_domestik_idr = sum_domestik_idr
            rec.sum_belanja_tkdn = sum_belanja_tkdn
            rec.real_impor_usd = real_impor_usd
            rec.real_domestik_idr = real_domestik_idr
            rec.real_belanja_tkdn = real_belanja_tkdn
            # persentase
            sum_domestik_usd = sum_domestik_idr / self.idr_id.rate * self.usd_id.rate
            sum_impor_domestik = sum_impor_usd + sum_domestik_usd
            if sum_impor_domestik > 0.0:
                rec.persen_sum_impor_usd = sum_impor_usd / sum_impor_domestik
                rec.persen_sum_domestik_idr = sum_domestik_usd / sum_impor_domestik
                rec.persen_sum_belanja_tkdn = (sum_belanja_tkdn / self.idr_id.rate * self.usd_id.rate) / sum_impor_domestik
            else:
                rec.persen_sum_impor_usd = 0.0
                rec.persen_sum_domestik_idr = 0.0
                rec.persen_sum_belanja_tkdn = 0.0
            # persentase realisasi
            real_domestik_usd = real_domestik_idr / self.idr_id.rate * self.usd_id.rate
            real_sum = real_impor_usd + real_domestik_usd
            if real_sum > 0.0:
                rec.persen_real_impor_usd = real_impor_usd / real_sum
                rec.persen_real_domestik_idr = real_domestik_usd / real_sum
                rec.persen_real_belanja_tkdn = (real_belanja_tkdn / self.idr_id.rate * self.usd_id.rate) / real_sum
            else:
                rec.persen_real_impor_usd = 0.0
                rec.persen_real_domestik_idr = 0.0
                rec.persen_real_belanja_tkdn = 0.0
            # capaian realisasi
            rec.capaian_real_impor_usd = real_impor_usd / sum_impor_usd if sum_impor_usd else 0.0
            rec.capaian_real_domestik_idr = real_domestik_idr / sum_domestik_idr if sum_domestik_idr else 0.0
            rec.capaian_real_belanja_tkdn = real_belanja_tkdn / sum_belanja_tkdn if sum_belanja_tkdn else 0.0


class purchase_plan(models.Model):
    _name = 'purchase.plan'
    _description = "Purchase Plan"

    year_id = fields.Many2one('purchase.plan.year')
    tahun = fields.Selection(related='year_id.name', store=True, string="Tahun")
    name = fields.Char(string='Judul', compute='_compute_name', store=True)
    category_id = fields.Many2one('purchase.category', 'Kategori')
    usd_id = fields.Many2one('res.currency', 'USD', compute='_compute_currency')
    idr_id = fields.Many2one('res.currency', 'IDR', compute='_compute_currency')
    impor_usd = fields.Float('Impor (USD)')
    domestik_idr = fields.Float('Domestik (IDR)')
    belanja_tkdn = fields.Float('Belanja TKDN (IDR)')
    real_impor_usd = fields.Float('Realisasi Impor (USD)', compute='_compute_purchase')
    real_domestik_idr = fields.Float('Realisasi Domestik (IDR)', compute='_compute_purchase')
    real_belanja_tkdn = fields.Float('Realisasi Belanja TKDN (IDR)', compute='_compute_purchase')
    realisasi_impor = fields.One2many('view.realisasi.belanja', 'plan_id', 'Realisasi Impor',
        domain=[('impor_domestik', '=', 'impor')])
    realisasi_domestik = fields.One2many('view.realisasi.belanja', 'plan_id', 'Realisasi Domestik',
        domain=[('impor_domestik', '=', 'domestik')])
    sum_impor_usd = fields.Float('Impor (USD)', compute='_compute_purchase')
    sum_domestik_idr = fields.Float('Domestik (IDR)', compute='_compute_purchase')
    sum_belanja_tkdn = fields.Float('Belanja TKDN (IDR)', compute='_compute_purchase')
    urutan = fields.Integer('Urutan', related='category_id.urutan', store=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    
    _sql_constraints = [
        ('unique_year_id_category_id', 'unique(year_id, category_id)', 'Tidak boleh ada kategori dalam tahun yang sama!'),
        ]

    def _tambah_total_per_tahun(self, tahun):
        # import web_pdb; web_pdb.set_trace()
        # Jika menambah tahun baru maka tambahkan TOTAL, PERSENTASE, dan CAPAIAN REALISASI
        if len(self.search([('tahun', '=', tahun), ('urutan', '>', 0)], limit=1)) == 0 and tahun:
            total_id = self.env.ref('metalindo_purchase.purchase_category_total')
            persen_id = self.env.ref('metalindo_purchase.purchase_category_persen')
            capai_id = self.env.ref('metalindo_purchase.purchase_category_capai')
            # Agar tidak berulang tanpa batas, maka ditambah lewat SQL
            sql = 'INSERT INTO purchase_plan (tahun, category_id, urutan, name) ' +\
                'VALUES (%s, %s, %s, %s), (%s, %s, %s, %s), (%s, %s, %s, %s)'
            self.env.cr.execute(sql, (
                tahun, total_id.id, total_id.urutan, 'Tahun ' + tahun + ' ' + total_id.name,
                tahun, persen_id.id, persen_id.urutan, 'Tahun ' + tahun + ' ' + persen_id.name,
                tahun, capai_id.id, capai_id.urutan, 'Tahun ' + tahun + ' ' + capai_id.name))

    @api.model_create_multi
    def create(self, vals_list):
        res = super(purchase_plan, self).create(vals_list)
        for vals in vals_list:
            self._tambah_total_per_tahun(vals.get('tahun'))
        return res

    def write(self, vals):
        res = super(purchase_plan, self).write(vals)
        self._tambah_total_per_tahun(vals.get('tahun'))
        return res

    @api.depends('tahun', 'category_id')
    def _compute_name(self):
        total_id = self.env.ref('metalindo_purchase.purchase_category_total')
        persen_id = self.env.ref('metalindo_purchase.purchase_category_persen')
        capai_id = self.env.ref('metalindo_purchase.purchase_category_capai')
        for rec in self:
            if rec.category_id not in (total_id, persen_id, capai_id):
                rec.name = 'Tahun ' + rec.tahun + ' Kategori ' + rec.category_id.name
            else:
                rec.name = 'Tahun ' + rec.tahun + ' ' + rec.category_id.name

    def _compute_currency(self):
        for rec in self:
            rec.usd_id = self.env.ref('base.USD')
            rec.idr_id = self.env.ref('base.IDR')

    # One2many bisa dibuat sebagai computed field dengan cara di bawah ini.
    # def _compute_real_ids:
    #     for rec in self:
    #         ids = [(4, line.id) for line in rec.category_id.purchase_ids]

    def _compute_purchase(self):
        # import web_pdb; web_pdb.set_trace()
        total_id = self.env.ref('metalindo_purchase.purchase_category_total')
        persen_id = self.env.ref('metalindo_purchase.purchase_category_persen')
        capai_id = self.env.ref('metalindo_purchase.purchase_category_capai')
        for rec in self:
            if rec.category_id in (total_id, persen_id, capai_id):
                # plan
                ids = self.env['purchase.plan'].search([('tahun', '=', rec.tahun)])
                sum_impor_usd = sum(ids.mapped('impor_usd')) or 0.0
                sum_domestik_idr = sum(ids.mapped('domestik_idr')) or 0.0
                sum_belanja_tkdn = sum(ids.mapped('belanja_tkdn')) or 0.0
                # realisasi
                ids = self.env['view.realisasi.belanja'].search([('tahun', '=', rec.tahun)])
                real_impor_usd = sum(ids.filtered(lambda x: x.impor_domestik == 'impor').mapped('price_subtotal_usd')) or 0.0
                domestik = ids.filtered(lambda x: x.impor_domestik == 'domestik')
                real_domestik_idr = sum(domestik.mapped('price_subtotal_idr')) or 0.0
                real_belanja_tkdn = sum([line.price_subtotal_idr * line.aml_id.move_id.partner_id.tkdn_persen for line in domestik]) or 0.0
                if rec.category_id == total_id:
                    rec.sum_impor_usd = sum_impor_usd
                    rec.sum_domestik_idr = sum_domestik_idr
                    rec.sum_belanja_tkdn = sum_belanja_tkdn
                    rec.real_impor_usd = real_impor_usd
                    rec.real_domestik_idr = real_domestik_idr
                    rec.real_belanja_tkdn = real_belanja_tkdn
                elif rec.category_id == persen_id:
                    sum_domestik_usd = sum_domestik_idr / self.idr_id.rate * self.usd_id.rate
                    sum_impor_domestik = sum_impor_usd + sum_domestik_usd
                    if sum_impor_domestik > 0.0:
                        rec.sum_impor_usd = sum_impor_usd / sum_impor_domestik * 100.0
                        rec.sum_domestik_idr = sum_domestik_usd / sum_impor_domestik * 100.0
                        rec.sum_belanja_tkdn = (sum_belanja_tkdn / self.idr_id.rate * self.usd_id.rate) / sum_impor_domestik * 100.0
                    else:
                        rec.sum_impor_usd = 0.0
                        rec.sum_domestik_idr = 0.0
                        rec.sum_belanja_tkdn = 0.0
                    real_domestik_usd = real_domestik_idr / self.idr_id.rate * self.usd_id.rate
                    real_sum = real_impor_usd + real_domestik_usd
                    if real_sum > 0.0:
                        rec.real_impor_usd = real_impor_usd / real_sum * 100.0
                        rec.real_domestik_idr = real_domestik_usd / real_sum * 100.0
                        rec.real_belanja_tkdn = (real_belanja_tkdn / self.idr_id.rate * self.usd_id.rate) / real_sum * 100.0
                    else:
                        rec.real_impor_usd = 0.0
                        rec.real_domestik_idr = 0.0
                        rec.real_belanja_tkdn = 0.0
                else:  # capaian realisasi
                    rec.sum_impor_usd = 0.0
                    rec.sum_domestik_idr = 0.0
                    rec.sum_belanja_tkdn = 0.0
                    rec.real_impor_usd = real_impor_usd / sum_impor_usd * 100.0 if sum_impor_usd else 0.0
                    rec.real_domestik_idr = real_domestik_idr / sum_domestik_idr * 100.0 if sum_domestik_idr else 0.0
                    rec.real_belanja_tkdn = real_belanja_tkdn / sum_belanja_tkdn * 100.0 if sum_belanja_tkdn else 0.0
            else:
                rec.sum_impor_usd = rec.impor_usd
                rec.sum_domestik_idr = rec.domestik_idr
                rec.sum_belanja_tkdn = rec.belanja_tkdn
                rec.real_impor_usd = sum(rec.realisasi_impor.mapped('price_subtotal_usd')) or 0.0
                rec.real_domestik_idr = sum(rec.realisasi_domestik.mapped('price_subtotal_idr')) or 0.0
                rec.real_belanja_tkdn = sum([line.price_subtotal_idr * line.aml_id.move_id.partner_id.tkdn_persen for line in rec.realisasi_domestik]) or 0.0


class view_realisasi_belanja(models.Model):
    _name = 'view.realisasi.belanja'
    _description = "View Realisasi Belanja"
    _auto = False
    
    aml_id = fields.Many2one('account.move.line', 'Account Move Line')
    tahun = fields.Char('Tahun')
    plan_id = fields.Many2one('purchase.plan', 'Purchase Plan')
    impor_domestik = fields.Char('Impor/Domestik')
    price_unit_idr = fields.Integer('Unit Price (IDR)', compute='_compute_price')
    price_unit_usd = fields.Integer('Unit Price (USD)', compute='_compute_price')
    price_subtotal_idr = fields.Integer('Total Price (IDR)', compute='_compute_price')
    price_subtotal_usd = fields.Integer('Total Price (USD)', compute='_compute_price')
    belanja_tkdn_idr = fields.Integer('Belanja TKDN (IDR)', compute='_compute_price')
    kab_kota = fields.Char(string='Kab/Kota Asal Belanja', compute='_compute_purchase_category')
    provinsi = fields.Char(string='Provinsi Asal Belanja', related='aml_id.move_id.partner_id.state_id.name')
    negara = fields.Char(string='Negara Asal Belanja', related='aml_id.move_id.partner_id.country_id.name')
    area_project = fields.Char(string='Area Project', compute='_compute_purchase_category')
    tkdn_sa = fields.Float(string='TKDN SA', compute='_compute_purchase_category')
    tkdn_s = fields.Float(string='TKDN S', compute='_compute_purchase_category')
    usd_id = fields.Many2one('res.currency', 'USD', compute='_compute_purchase_category')
    idr_id = fields.Many2one('res.currency', 'IDR', compute='_compute_purchase_category')
    jenis_barang = fields.Char(string='Jenis Barang', compute='_compute_purchase_category')
    kode_hs = fields.Char(string='Kode HS', compute='_compute_purchase_category')
    spec = fields.Char('Spesifikasi', compute='_compute_purchase_category')
    quantity = fields.Float(string='Kuantitas', related='aml_id.quantity')
    partner_id = fields.Many2one('res.partner', 'Produsen/Supplier', related='aml_id.move_id.partner_id')
    company_id = fields.Many2one('res.company', 'Company')
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s AS 
            SELECT row_number() over () as id
                , aml.id as aml_id
                , pp.tahun
                , pp.id as plan_id
                , aml.impor_domestik
                , aml.company_id
            FROM (select id
                , date
                , move_id
                , purchase_category_id
                , impor_domestik
                , company_id
                from account_move_line
                where state = 'posted'
                and invoice_type = 'in_invoice'
                and purchase_category_id is not null
                ) aml
            --JOIN LATERAL (select aip.invoice_id
            --    , ap.payment_date as paid_date
            --    from account_payment ap
            --    join account_invoice_payment_rel aip on ap.id = aip.payment_id
            --    where aip.invoice_id = aml.move_id
            --    order by ap.payment_date desc limit 1) p on p.invoice_id = aml.move_id
            JOIN purchase_plan pp 
                on aml.purchase_category_id = pp.category_id
                --AND pp.tahun = to_char(p.paid_date, 'YYYY')
                AND pp.tahun = to_char(aml.date, 'YYYY')
                AND pp.company_id = aml.company_id""" % self._table)

    def _compute_purchase_category(self):
        for rec in self:
            rec.kab_kota = rec.aml_id.move_id.partner_id.city or rec.aml_id.move_id.partner_id.code_id.name
            rec.area_project = 'Lapaopao RKEF Smelter FeNi Project'
            rec.tkdn_sa = 0.0
            rec.tkdn_s = 0.0
            rec.usd_id = self.env.ref('base.USD')
            rec.idr_id = self.env.ref('base.IDR')
            if rec.aml_id.move_id.partner_id.tkdn == 'self_assessment':
                rec.tkdn_sa = rec.aml_id.move_id.partner_id.tkdn_persen
            if rec.aml_id.move_id.partner_id.tkdn == 'certificate':
                rec.tkdn_s = rec.aml_id.move_id.partner_id.tkdn_persen
            rec.jenis_barang = rec.aml_id.product_id.name or rec.aml_id.name
            rec.kode_hs = rec.aml_id.product_id.product_tmpl_id.hs_code or rec.aml_id.hs_code
            if rec.aml_id.product_id:
                if rec.aml_id.product_id.product_tmpl_id.description:
                    rec.spec = rec.aml_id.product_id.product_tmpl_id.description
                else:
                    rec.spec = rec.aml_id.product_id.name
            else:
                rec.spec = rec.aml_id.name

    def _compute_price(self):
        # import web_pdb; web_pdb.set_trace()
        idr_id = self.env.ref('base.IDR')
        usd_id = self.env.ref('base.USD')
        for rec in self:
            currency_id = rec.aml_id.move_id.currency_id
            if currency_id.rate > 0.0:
                if currency_id == idr_id:
                    rec.price_unit_idr = round(rec.aml_id.price_unit)
                    rec.price_subtotal_idr = round(rec.aml_id.price_subtotal)
                else:
                    rec.price_unit_idr = round((idr_id.rate / currency_id.rate) * rec.aml_id.price_unit)
                    rec.price_subtotal_idr = round((idr_id.rate / currency_id.rate) * rec.aml_id.price_subtotal)
                if currency_id == usd_id:
                    rec.price_unit_usd = round(rec.aml_id.price_unit)
                    rec.price_subtotal_usd = round(rec.aml_id.price_subtotal)
                else:
                    rec.price_unit_usd = round((usd_id.rate / currency_id.rate) * rec.aml_id.price_unit)
                    rec.price_subtotal_usd = round((usd_id.rate / currency_id.rate) * rec.aml_id.price_subtotal)
            else:
                rec.price_unit_idr = round(rec.aml_id.price_unit)
                rec.price_unit_usd = round(rec.aml_id.price_unit)
                rec.price_subtotal_idr = round(rec.aml_id.price_subtotal)
                rec.price_subtotal_usd = round(rec.aml_id.price_subtotal)
            rec.belanja_tkdn_idr = round(rec.price_subtotal_idr * rec.aml_id.move_id.partner_id.tkdn_persen)


class purchase_plan_create_wizard(models.TransientModel):
    _name = 'purchase.plan.create.wizard'
    _description = 'Create purchase plan for all categories'

    def _selection_tahun(self):
        # import web_pdb; web_pdb.set_trace()
        total_id = self.env.ref('metalindo_purchase.purchase_category_total')
        list_tahun = list(set(self.env['purchase.plan'].sudo().search([
            ('category_id', '=', total_id.id)
            ], order='tahun').mapped('tahun')))
        tahun = False
        if len(list_tahun) > 0:
            tahun = list_tahun[0]
        if not tahun:
            tahun = fields.Date.context_today(self).strftime('%Y')
        select_tahun = []
        for n in range(len(list_tahun)+3):
            str_tahun = str(int(tahun) + n)
            select_tahun.append((str_tahun, str_tahun))
        return select_tahun

    tahun = fields.Selection(selection=lambda self: self._selection_tahun(), string='Tahun')

    def button_create(self):
        # import web_pdb; web_pdb.set_trace()
        if self.tahun:
            cat_ids = [x.category_id.id for x in self.env['purchase.plan'].search([
                ('tahun', '=', self.tahun), ('urutan', '=', 0)
                ])]
            if len(cat_ids) > 0:
                cat_ids = self.env['purchase.category'].search([
                    ('id', 'not in', cat_ids), ('urutan', '=', 0)])
            else:
                cat_ids = self.env['purchase.category'].search([('urutan', '=', 0)])
            for cat_id in cat_ids:
                self.env['purchase.plan'].create({
                    'tahun': self.tahun,
                    'category_id': cat_id.id,
                    })
