from odoo import api, fields, models, _


READONLY_STATES = {
    'purchase': [('readonly', True)],
    'done': [('readonly', True)],
    'cancel': [('readonly', True)],
}


class purchase_requisition(models.Model):
    _inherit = 'purchase.requisition'


    # purchase_ids = fields.Many2many('purchase.order',string="Purchase Orders",compute="_get_purchase")
    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm', help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")
    date_end = fields.Datetime(string='Closed Date', tracking=True)
    user_id = fields.Many2one(
        'res.users', string='Buyer',
        default=lambda self: self.env.user, check_company=True)
    delivery_point_id = fields.Many2one('res.partner','Delivery Point',domain=[('is_delivery_point','=',True)])
    cheapest_purchase_id = fields.Many2one('purchase.order',compute="get_cheapest_purchase")
    vendor_id = fields.Many2one('res.partner', string="Vendor", domain="['|', ('company_id', '=', False), ('company_id', '=', company_id),('vendor_code','!=',False),('vendor_code','!=','New')]")
    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint','Reordering Rule')
    recommended = fields.Boolean()
    is_tender = fields.Boolean(compute='_compute_is_tender')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms')


    @api.onchange('delivery_point_id')
    def _onchange_delivery_point_id(self):
        if self.delivery_point_id:
            if self.delivery_point_id.picking_type_id:
                self.picking_type_id = self.delivery_point_id.picking_type_id

    @api.constrains('user_id')
    def update_source_buyer(self):
        res = super().update_source_buyer()
        for this in self:
            for line in this.line_ids:
                if line.recommend_qty_id:
                    line.recommend_qty_id.write({'procurement_user_id': this.user_id.id})
        return res

    @api.depends('type_id')
    def _compute_is_tender(self):
        for rec in self:
            if rec.type_id == self.env.ref('metalindo_purchase.call_for_tender'):
                rec.is_tender = True
            else:
                rec.is_tender = False

    def get_cheapest_purchase(self):
        for rec in self:
            if rec.purchase_ids:
                cheapest_purchase_id = False
                for purchase_id in rec.purchase_ids:
                    if not cheapest_purchase_id:
                        cheapest_purchase_id = purchase_id
                        continue
                    if purchase_id.get_company_currency_amount() < cheapest_purchase_id.get_company_currency_amount():
                        cheapest_purchase_id = purchase_id
                rec.cheapest_purchase_id = cheapest_purchase_id
                
    # def _get_purchase(self):
    #     for rec in self:
    #         purchase_ids = self.env['purchase.order'].search([('requisition_id','=',self.id)])
    #         rec.purchase_ids = purchase_ids

    def closed_for_purchase(self):
        for rec in self:
            for line in rec.line_ids:
                if line.product_qty != line.purchased_qty:
                    return False
        return True

    def show_bid_tabulation(self):
        return self.env.ref('metalindo_purchase.bid_tabulation_report_id').report_action(self)
        
    def get_vendor_ids(self):
        return self.purchase_ids.mapped('partner_id')

    def get_vendor_prices(self):
        prices = {}
        for purchase in self.purchase_ids:
            directcharge = purchase.is_directcharge
            for line in purchase.order_line:
                product_key = line.product_id.id
                if directcharge:
                    product_key = '%s-%s'%(line.product_id.id,line.name)
                val = {
                    product_key : {
                        'price': line.price_unit,
                        'currency_id' : line.currency_id,
                    }
                }
                if purchase.partner_id.id in prices.keys():
                    prices[purchase.partner_id.id].update(val)
                else:
                    prices[purchase.partner_id.id] = val
        return prices

    def get_purchase_prices(self):
        prices = {}
        for purchase in self.purchase_ids:
            for line in purchase.order_line:
                product_key = line.product_id.id
                val = {
                    product_key : {
                        'price': line.price_unit,
                        'currency_id' : line.currency_id,
                    }
                }
                prices[purchase.id] = val
        return prices


class purchase_requisition_line(models.Model):
    _inherit = 'purchase.requisition.line'


    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint')
    recommend_qty_id = fields.Many2one('recommend.qty')
    recommend_qty_ids = fields.Many2many('recommend.qty')
    purchase_request_id = fields.Many2one('purchase.request')
    purchase_category_id = fields.Many2one('purchase.category', 'Purchase Category')
    hs_code_id = fields.Many2one('masterlist.product', string='HS Code')
    analytic_id = fields.Many2one('account.analytic.account', 'Cost Center')
    hs_code = fields.Char()


    @api.model_create_multi
    def create(self, vals_list):
        # import web_pdb; web_pdb.set_trace()
        res = super(purchase_requisition_line, self).create(vals_list)
        vals = vals_list[0]
        if vals.get('purchase_category_id') or vals.get('hs_code'):
            res.product_id.product_tmpl_id.sudo().write({
                'purchase_category_id': vals.get('purchase_category_id'),
                'hs_code': vals.get('hs_code'),
                })
        res.write_purchase_ref()
        return res

    def write(self, vals):
        # import web_pdb; web_pdb.set_trace()
        res = super(purchase_requisition_line, self).write(vals)
        if vals.get('purchase_category_id') or vals.get('hs_code'):
            self.product_id.product_tmpl_id.sudo().write({
                'purchase_category_id': vals.get('purchase_category_id'),
                'hs_code': vals.get('hs_code'),
                })
        return res

    @api.onchange('product_id')
    def _onchange_product_id_purchase_category_id(self):
        self.purchase_category_id = self.product_id.product_tmpl_id.purchase_category_id

    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        res = super(purchase_requisition_line,self)._prepare_purchase_order_line(name, product_qty, price_unit, taxes_ids)
        res['product_qty'] =  max(0,self.product_qty - self.qty_ordered)
        res['purchase_category_id'] = self.purchase_category_id.id or self.product_id.product_tmpl_id.purchase_category_id.id
        res['hs_code'] = self.hs_code or self.product_id.product_tmpl_id.hs_code
        return res
    
    def write_purchase_ref(self):
        for this in self:
            if  this.recommend_qty_id:
                this.recommend_qty_id.write({'requisition_id': this.requisition_id.id})
                if this.recommend_qty_id.state == 'Ready to Purchase':
                    this.recommend_qty_id.write({'state': 'On Tender'})

            if this.recommend_qty_ids:
                ready_to_purchase = this.recommend_qty_ids.filtered_domain([('state', '=', 'Ready to Purchase')])
                on_purchase = this.recommend_qty_ids.filtered_domain([('state', '=', 'In Procurement')])
                if ready_to_purchase:
                    ready_to_purchase.write({'requisition_id' : this.requisition_id.id, 'state' : 'On Tender'})
                if on_purchase:
                    on_purchase.write({'requisition_id' : this.requisition_id.id})

    def reset_recommend(self):
        for this in self:
            if this.recommend_qty_id:
                this.recommend_qty_id.write({'requisition_id' : False})
                if this.recommend_qty_id.state == 'On Tender':
                    this.recommend_qty_id.write({'state' : 'Ready to Purchase'})

            if this.recommend_qty_ids:
                on_tender = this.recommend_qty_ids.filtered_domain([('state', '=', 'On Tender')])
                on_purchase = this.recommend_qty_ids.filtered_domain([('state', '=', 'In Procurement')])
                if on_tender:
                    on_tender.write({'requisition_id' : False, 'state' : 'Ready to Purchase'})
                if on_purchase:
                    on_purchase.write({'requisition_id': False})

    def unlink(self):
        self.reset_recommend()
        return super(purchase_requisition_line, self).unlink()
