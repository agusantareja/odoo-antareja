from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import base64
from odoo.tools import file_open, DEFAULT_SERVER_DATETIME_FORMAT, get_lang
import tempfile
from PyPDF2 import PdfFileMerger
import logging
_logger = logging.getLogger(__name__)


READONLY_STATES = {
    'purchase': [('readonly', True)],
    'done': [('readonly', True)],
    'cancel': [('readonly', True)],
}


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    price_view = fields.Float('Price', compute="_compute_price_unit_and_date_planned_and_name", readonly=False, store=True)
    discount = fields.Float('Discount')
    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint')
    recommend_qty_id = fields.Many2one('recommend.qty')
    recommend_qty_ids = fields.Many2many('recommend.qty')
    purchase_request_id = fields.Many2one('purchase.request')
    umkm_id = fields.Many2one('kegiatan.umkm', 'UMKM Category')
    is_umkm = fields.Boolean(compute='_compute_is_umkm')
    purchase_category_id = fields.Many2one('purchase.category', 'Purchase Category')
    hs_code_id = fields.Many2one('masterlist.product', string='HS Code')
    hs_code = fields.Char()
    analytic_id = fields.Many2one('account.analytic.account', string='Cost Center')
    source = fields.Char(string='Source', compute='compute_source')
    discount_persen = fields.Float('Discount %')
    discount_type = fields.Selection(string='Discount Type', selection=[('item', 'Per Item'), ('global', 'Global')], default='item', related='order_id.discount_type', store=True)
    incoterm_id = fields.Many2one('account.incoterms', string='Incoterm', related='order_id.incoterm_id')
    delivery_point_id = fields.Many2one('res.partner','Delivery Point', related='order_id.delivery_point_id')
    delivery_days = fields.Integer(string='Delivery Days', related='order_id.delivery_days')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', related='order_id.payment_term_id')
    item_no = fields.Integer(string='Item No')
    remarks = fields.Text(string='Remarks')
    description = fields.Text(string='Description', compute='_compute_description', readonly=False, store=True)
    print_po_date = fields.Datetime(string='PO Slip printed on', related='order_id.print_po_date')
    delivery_time = fields.Integer(string='Delivery Time (Days)')
    manufacturer_id = fields.Many2one(comodel_name='res.partner', compute='_compute_description', store=True)
    part_number = fields.Char(compute='_compute_description', store=True)
    po_incoming_qty = fields.Float(compute='compute_po_incoming_qty', store=True)


    @api.depends('product_qty', 'qty_received')
    def compute_po_incoming_qty(self):
        for this in self:
            this.po_incoming_qty = 0
            if this.product_qty > this.qty_received:
                this.po_incoming_qty = this.product_qty - this.qty_received

    @api.constrains('delivery_time')
    def constrains_delivery_time(self):
        for rec in self:
            if rec.print_po_date:
                rec.date_planned = rec.print_po_date + timedelta(days=rec.delivery_time)

    @api.depends('product_id')
    def _compute_description(self):
        for rec in self:
            rec.description = rec.product_id.description.strip() if rec.product_id.description else rec.product_id.description
            rec.manufacturer_id = rec.product_id.manufacturer_id
            rec.part_number = rec.product_id.part_number

    def _get_po_line_moves(self):
        self.ensure_one()
        picking_type_id = self.env.ref('stock.picking_type_in').id
        moves = self.move_ids.filtered(lambda m: m.product_id == self.product_id and m.picking_type_id.id == picking_type_id)
        if self._context.get('accrual_entry_date'):
            moves = moves.filtered(lambda r: fields.Date.to_date(r.date) <= self._context['accrual_entry_date'])
        return moves

    @api.depends('product_qty', 'product_uom')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if not line.product_id or line.invoice_lines:
                continue
            params = {'order_id': line.order_id}
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date(),
                uom_id=line.product_uom,
                params=params)

            if seller or not line.date_planned:
                line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # If not seller, use the standard price. It needs a proper currency conversion.
            if not seller:
                unavailable_seller = line.product_id.seller_ids.filtered(
                    lambda s: s.partner_id == line.order_id.partner_id)
                if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
                    # Avoid to modify the price unit if there is no price list for this partner and
                    # the line has already one to avoid to override unit price set manually.
                    continue
                po_line_uom = line.product_uom or line.product_id.uom_po_id
                price_unit = line.env['account.tax']._fix_tax_included_price_company(
                    line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
                    line.product_id.supplier_taxes_id,
                    line.taxes_id,
                    line.company_id,
                )
                if not line.price_unit:
                    line.price_unit = line.price_view = line.currency_id._convert(
                        price_unit,
                        line.currency_id,
                        line.company_id,
                        line.date_order,
                    )
                continue
            
            if not line.price_unit:
                price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price, line.product_id.supplier_taxes_id, line.taxes_id, line.company_id) if seller else 0.0
                price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order)
                line.price_unit = line.price_view = seller.product_uom._compute_price(price_unit, line.product_uom)

            # record product names to avoid resetting custom descriptions
            default_names = []
            vendors = line.product_id._prepare_sellers({})
            for vendor in vendors:
                product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
            if not line.name or line.name in default_names:
                product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))

    # @api.depends("discount_persen")
    # def _compute_amount(self):
    #     return super()._compute_amount()

    # def _convert_to_tax_base_line_dict(self):
    #     for rec in self:
    #         vals = super()._convert_to_tax_base_line_dict()
    #         vals.update({
    #             "price_unit": rec.price_view,
    #             "discount": rec.discount_persen,
    #         })
    #         return vals

    @api.onchange('discount_persen', 'price_view')
    @api.constrains('discount_persen', 'price_view')
    def onchange_discount(self):
        for rec in self:
            rec.discount = (rec.price_view * rec.product_qty) * rec.discount_persen
            rec.price_unit = rec.price_view - (rec.discount/rec.product_qty)

    @api.depends('recommend_qty_id','recommend_qty_ids', 'mr_line_id')
    def compute_source(self):
        for rec in self:
            rec.source =  None
            if rec.recommend_qty_ids:
                rec.source = ', '.join(rec.recommend_qty_ids.mapped('name'))
            elif rec.recommend_qty_id:
                rec.source = rec.recommend_qty_id.name
            elif rec.mr_line_id:
                rec.source = f'{rec.mr_line_id.mr_id.name}-{rec.mr_line_id.no}'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(purchase_order_line, self).create(vals_list)
        if vals_list:
            vals = vals_list[0]
            if vals.get('purchase_category_id') or vals.get('hs_code_id'):
                res.product_id.product_tmpl_id.sudo().write({
                    'purchase_category_id': vals.get('purchase_category_id'),
                    'product_hscode_id': vals.get('hs_code_id'),
                    })
        res.write_purchase_ref()
        return res

    def write(self, vals):
        res = super(purchase_order_line, self).write(vals)
        if vals.get('purchase_category_id') or vals.get('hs_code_id'):
            self.product_id.product_tmpl_id.sudo().write({
                'purchase_category_id': vals.get('purchase_category_id'),
                'product_hscode_id': vals.get('hs_code_id'),
                })
        return res

    def write_purchase_ref(self):
        for line in self.filtered(lambda r: not r.order_id.is_rfq_tender):
            if line.recommend_qty_id:
                line.recommend_qty_id.write({'purchase_id' : line.order_id.id, 'state' : 'In Procurement'})
            if line.recommend_qty_ids:
                line.recommend_qty_ids.write({'purchase_id' : line.order_id.id, 'state' : 'In Procurement'})

    def unlink(self):
        not_rfq_tender = self.filtered(lambda r: not r.order_id.is_rfq_tender)
        not_from_tender = not_rfq_tender.filtered(lambda r: not r.order_id.requisition_id)
        targets = not_from_tender.recommend_qty_id | not_from_tender.recommend_qty_ids
        targets.write({'purchase_id': False, 'state': 'Ready to Purchase'})

        for line in not_rfq_tender.filtered(lambda r: r.order_id.requisition_id):
            if (line.tender_line_id.outstanding_qty + line.product_qty) == line.tender_line_id.product_qty:
                targets = line.recommend_qty_id | line.recommend_qty_ids
                targets.write({'purchase_id': False, 'state': 'On Tender', 'requisition_id': line.order_id.requisition_id.id})

        return super(purchase_order_line, self).unlink()

    def write_received(self):
        for line in self.filtered(lambda r: not r.order_id.is_rfq_tender):
            if line.recommend_qty_id:
                if line.qty_received >= line.product_qty:
                    line.recommend_qty_id.write({'state' : 'Done', 'qty_done' : line.product_qty})
            if line.recommend_qty_ids:
                records = line.recommend_qty_ids.filtered_domain([('product_id', '=', line.product_id.id)]).sorted('id')
                polines_all = self.search([
                    ('state', '!=', 'cancel'),
                    ('product_id', '=', line.product_id.id),
                    ('recommend_qty_ids', 'in', records.ids)])
                overall_received = sum(p.qty_received or 0.0 for p in polines_all)
                remaining = overall_received
                for rec in records:
                    target = float(rec.bro_purchase_qty or 0.0)
                    take   = min(target, max(remaining, 0.0))
                    remaining -= take
                    rec.write({'qty_done': take, 'state': 'Done' if (target > 0 and take >= target) else 'In Procurement'})

    @api.onchange('product_id')
    def _onchange_product_id_purchase_category_id(self):
        self.purchase_category_id = self.product_id.product_tmpl_id.purchase_category_id
        self.hs_code_id = self.product_id.product_tmpl_id.product_hscode_id.id

    def _prepare_account_move_line(self, move=False):
        res = super(purchase_order_line, self)._prepare_account_move_line(move)
        res['purchase_category_id'] = self.purchase_category_id.id or self.product_id.product_tmpl_id.purchase_category_id.id
        # res['hs_code_id'] = self.hs_code_id.id or self.product_id.product_tmpl_id.product_hscode_id.id
        return res

    @api.constrains("umkm_id")
    def _check_umkm_id(self):
        for rec in self:
            if rec.order_id.partner_id.code_id.code == 'UMKM' and not rec.umkm_id:
                raise ValidationError('UMKM Category untuk %s harus diisi.' % rec.name)

    def _compute_is_umkm(self):
        for rec in self:
            if rec.order_id.partner_id.code_id.code == 'UMKM':
                rec.is_umkm = True
            else:
                rec.is_umkm = False

    def get_requisition_line(self):
        for line in self.order_id.requisition_id.line_ids:
            if self.product_id == line.product_id:
                return line

    @api.constrains('product_id','order_id')
    def set_procurement_user(self):
        default_user_id = self.product_id.categ_id.procurement_user_id
        if default_user_id:
            self.order_id.user_id = default_user_id.id


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    delivery_days = fields.Integer(string='Delivery Days', tracking=True)
    date_end = fields.Datetime('Closed Date', index=True)
    # incoterm_id = fields.Many2one('account.incoterms', 'Freight Method', help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")
    delivery_point_id = fields.Many2one('res.partner','Delivery Point',domain=[('is_delivery_point','=',True)])
    discount_type = fields.Selection([('item','Per Item'),('global','Global')], string='Discount Type', default='item')
    discount = fields.Float('Discount')
    discount_persen = fields.Float('Discount %')
    discount_total = fields.Float('Total Discount',compute="_amount_all", compute_sudo=True)
    delivery_point = fields.Many2one('res.partner','Delivery Point')
    requisition_type_id = fields.Many2one('purchase.requisition.type','Requisition Type',related="requisition_id.type_id")
    picking_state = fields.Selection([
        ('transit','In Transit'),
        ('received','Received')
    ],string="Transfer Status")
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, states=READONLY_STATES, change_default=True, tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id),('vendor_code','!=',False),('vendor_code','!=','New')]", help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint','Reordering Rule')
    recommended = fields.Boolean()
    exclusive = fields.Selection(related='requisition_id.type_id.exclusive')
    requisition_state = fields.Selection(related='requisition_id.state')
    print_po_date = fields.Datetime(string='PO Slip printed on', copy=False)
    taxes_html_backend = fields.Html(string='Taxes Html Backend', sanitize=False, compute='_compute_taxes_html', store=False)
    taxes_html_frontend = fields.Html(string='Taxes Html Frontend', sanitize=False, compute='_compute_taxes_html', store=False)
    subtotal = fields.Float(string='Subtotal', compute='compute_subtotal')
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('sent', 'RFQ Sent'),
        ('waiting_for_approval','Waiting For Approval'),
        ('to approve', 'To Approve'),
        ('approved','Approved'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('reject', 'Rejected'),
        ('cancel', 'Cancelled'),
    ])
    picking_type_id = fields.Many2one('stock.picking.type', 'Delivery Method')
    po_report = fields.Binary(string='PO Report', attachment=True, copy=False)
    po_report_filename = fields.Char('PO Report Filename', copy=False)
    vendor_acknowledge_report = fields.Binary(string='Vendor Acknowledge Report', attachment=True, copy=False)
    vendor_acknowledge_report_filename = fields.Char('Vendor Acknowledge Report Filename', copy=False)
    po_type = fields.Selection([
        ('service','Service'),
        ('consu','Goods'),
    ], string='PO Type', tracking=True)
    rfq_name = fields.Char(string='RFQ Name')
    current_user_is_buyer = fields.Boolean(compute='_compute_current_user_is_buyer')
    # implement compute_is_scm_manager_approve di metalindo_purchase_approval
    is_scm_manager_approve = fields.Boolean(string='SCM Manager Approve', store=False)
    is_rush_order = fields.Boolean(string='Rush Order', tracking=1)
    is_scm_buyer = fields.Boolean(compute='compute_is_scm_buyer')
    is_from_bro = fields.Boolean(string='From BRO', compute='_compute_po_from_bro', store=True)


    @api.depends('order_line', 'order_line.recommend_qty_id', 'order_line.recommend_qty_ids')
    def _compute_po_from_bro(self):
        for this in self:
            this.is_from_bro = bool(
                this.order_line.mapped('recommend_qty_id') or
                this.order_line.mapped('recommend_qty_ids')
            )
            
    def compute_is_scm_buyer(self):
        for this in self:
            this.is_scm_buyer = self.env.user.has_group('metalindo_inventory.group_metalindo_procurement_engineer')

    """ move to metalindo_purchase_approval
    def compute_is_scm_manager_approve(self):
        for this in self:
            this.is_scm_manager_approve = False
            group_category_scm = self.env.ref('metalindo_inventory.module_category_metalindo_inventory')
            #grup scm manager tidak bisa di search by xml id karena sepertinya create manual grupnya
            group_scm_manager = self.env['res.groups'].sudo().search([('category_id', '=', group_category_scm.sudo().id), ('name', 'like', 'Manager')])
            if group_scm_manager:
                approve_scm_manager = this.approval_ids.filtered(lambda x: x.group_id == group_scm_manager and x.sts == '2')
                if approve_scm_manager:
                    if this.state in ('waiting_for_approval','purchase','done'):
                        this.is_scm_manager_approve = True
                else:
                    if this.state in ('purchase','done'):
                        this.is_scm_manager_approve = True
    """

    @api.constrains('user_id')
    def update_source_buyer(self):
        res = super().update_source_buyer()
        for this in self:
            for line in this.order_line:
                if line.recommend_qty_ids:
                    for recom in line.recommend_qty_ids:
                        recom.write({'procurement_user_id': this.user_id.id})
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(purchase_order, self).create(vals_list)
        if not self.env.context.get('from_tender'):
            res.generate_name()      
        no = 1
        for line in res.order_line:
            line.item_no = no
            no += 1
        res.validation_order_line()
        return res
    
    def toggle_r_prefix(self,code, triger_rush_order):
        rush_order = 'R-'
        parts = code.split('-')
        
        if len(parts) >= 5 and not triger_rush_order:
            if parts[-2] == 'R' and parts[-1].isdigit():
                parts = parts[:-2] + [parts[-1]]
                return '-'.join(parts)
        elif len(parts) == 5 and triger_rush_order:
            parts[-1] = rush_order + parts[-1]
            return '-'.join(parts)
        return code

    def write(self, vals):
        if 'is_rush_order' in vals:
            triger_rush_order = vals.get('is_rush_order')
            vals['name'] = self.toggle_r_prefix(self.name, triger_rush_order)

        res = super(purchase_order, self).write(vals)
        no = 1
        for line in self.order_line:
            line.item_no = no
            no += 1

        if 'po_type' in vals:
            self.generate_name()
        self.validation_order_line()
        return res
    
    @api.onchange('po_type')
    def _onchange_po_type(self):
        if self.po_type and not self.is_from_bro and not self.is_from_pr:
            #reset line_ids
            self.order_line = False

    def button_approve(self, force=False):
        self.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
        # self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})
        if not self.consignment:
            self._create_picking()

        for po_line in self.order_line:
            for move in po_line.move_ids:
                move.write({'analytic': po_line.analytic_distribution})
        return {}

    def generate_name(self):
        A = "I"
        # Since a PO must exclusively contain PR items or BRO items, checking only the first
        # `order_line` should be sufficient.
        if self.order_line and self.order_line[0].mr_line_id:
            A = "P"
        if self.env.context.get('create_po_manual'):
            A= "P"
            
        JP = "S"
        if self.po_type == 'consu':
            JP = "G"
        THN = datetime.now().strftime("%y")
        sequence_code = f"CMP-PO-{A}-{JP}-{THN}"
        sequence_id = self.env['ir.sequence'].search([('code', '=', sequence_code)])
        if not sequence_id:
            sequence_id = self.env['ir.sequence'].sudo().create({
                'name': sequence_code,
                'code': sequence_code,
                'prefix': sequence_code,
                'padding': 3,
            })
        name = self.env['ir.sequence'].next_by_code(sequence_code)
        if self.is_rush_order:
            triger_rush_order = self.is_rush_order
            name = self.toggle_r_prefix(name, triger_rush_order)
        self.name = name

    @api.constrains("state")
    def _delete_attachment(self):
        for rec in self:
            if rec.state == 'purchase':
                # Reset the reports without deleting the previous ones
                rec.po_report = False
                rec.po_report_filename = False
                rec.vendor_acknowledge_report = False
                rec.vendor_acknowledge_report_filename = False

    def button_print_po(self):
        for rec in self:
            if not rec.po_report:
                rec.print_po_date = datetime.now()
                rec.order_line.constrains_delivery_time()
                rec.generate_po_slip()
            return {
                'type': 'ir.actions.act_url',
                'name': 'contract',
                'url': '/web/content/%s/%s/po_report/%s?download=true' %(rec._name, rec.id, rec.po_report_filename),
            }

    def button_print_vendor_acknowledge(self):
        for rec in self:
            if rec.vendor_acknowledge_report:
                return {
                    'type': 'ir.actions.act_url',
                    'name': 'contract',
                    'url': '/web/content/%s/%s/vendor_acknowledge_report/%s?download=true' %(rec._name, rec.id, rec.vendor_acknowledge_report_filename),
                }
            else:
                pdf = self.env['ir.actions.report'].sudo()._render_qweb_pdf('metalindo_purchase.metalindo_action_report_vendor_acknowledge', int(rec.id))
                b64_pdf = base64.b64encode(pdf[0])
                vendor_acknowledge_report_filename = 'Vendor Acknowledge - %s - %s.pdf' % (rec.partner_id.name or '', rec.name)
                rec.write({
                    'vendor_acknowledge_report': b64_pdf,
                    'vendor_acknowledge_report_filename': vendor_acknowledge_report_filename,
                })

                attachment_obj = self.env['ir.attachment'].sudo().search([
                    ('res_id', '=', rec.id),
                    ('res_model', '=', rec._name),
                    ('res_field', '=', 'vendor_acknowledge_report'),
                ])
                attachment = attachment_obj.copy()
                attachment.write({
                    'res_field': None,
                    'name': attachment.create_date.strftime('%Y-%m-%d ') + vendor_acknowledge_report_filename
                })

                return self.env.ref('metalindo_purchase.metalindo_action_report_vendor_acknowledge').report_action(self)

    @api.depends('order_line.price_subtotal')
    def compute_subtotal(self):
        for rec in self:
            rec.subtotal = sum(rec.order_line.mapped('price_subtotal')) or 0.0

    def _prepare_picking(self):
        res = super(purchase_order,self)._prepare_picking()
        res['purchase_id'] = self.id
        return res
    
    @api.onchange('discount_type')
    @api.constrains("discount_type")
    def onchange_discount_type(self):
        for rec in self:
            if not rec.requisition_id:
                if rec.discount_type == 'global':
                    for line in rec.order_line:
                        line.discount_persen = rec.discount_persen
                        line.onchange_discount()
                elif rec.discount_type == 'item':
                    rec.discount_persen = 0.0

    @api.onchange('discount_persen')
    @api.constrains('discount_persen')
    def onchange_discount_persen(self):
        for rec in self:
            if not rec.requisition_id and rec.discount_type == 'global':
                for line in rec.order_line:
                    line.discount_persen = rec.discount_persen
                    line.onchange_discount()

    def get_list_taxes(self):
        result = []
        for rec in self:
            taxes_obj = rec.order_line.mapped('taxes_id')
            if taxes_obj:
                for tax in self.env['account.tax'].browse(taxes_obj.ids):
                    amount = 0.0
                    for line in rec.order_line:
                        if tax.id in line.taxes_id.ids:
                            amount += line.price_tax

                    # amount = '{:,.2f}'.format(amount)
                    result.append({
                        'label': tax.name,
                        'amount': amount,
                    })
        return result

    @api.depends('order_line.taxes_id')
    def _compute_taxes_html(self):
        for rec in self:
            rec.taxes_html_backend = False
            rec.taxes_html_frontend = False


            taxes_backend = ""
            taxes_frontend = ""


            taxes_obj = rec.order_line.mapped('taxes_id')
            if taxes_obj:
                for tax in self.env['account.tax'].browse(taxes_obj.ids):
                    amount = 0.0
                    for line in rec.order_line:
                        if tax.id in line.taxes_id.ids:
                            subtotal = line.product_qty * line.price_view
                            price_tax = (subtotal - (subtotal * line.discount_persen / 100)) * tax.amount / 100
                            amount += price_tax

                    amount = '{:,.2f}'.format(amount)

                    taxes_backend += """
                        <tr>
                            <td class="o_td_label">
                                <label class="o_form_label o_tax_total_label">{label}</label>
                            </td>
                            <td class="o_list_monetary">
                                <span style="white-space: nowrap; font-weight: bold;">Rp&nbsp;{amount}</span>
                            </td>
                        </tr>
                    """.format(label=tax.name, amount=amount)
                    
                    taxes_frontend += """
                        <div class="row">
                            <div class="col-lg-2">
                            </div>
                            <div class="col-lg-8" style="text-align : right">
                                <strong>{label} : </strong>
                            </div>
                            <div class="col-lg-2">
                                <input type="text" value="{amount}" class="form-control number-format" style="text-align : right" readonly="1" />
                            </div>
                        </div>
                    """.format(label=tax.name, amount=amount)



            rec.taxes_html_backend = """
                <table class="oe_right" width="100%">
                    <tbody>
                        {taxes_backend}
                    </tbody>
                </table>
            """.format(taxes_backend=taxes_backend)

            rec.taxes_html_frontend = """
                {taxes_frontend}
            """.format(taxes_frontend=taxes_frontend)

    @api.onchange('delivery_point_id')
    def _onchange_delivery_point_id(self):
        if self.delivery_point_id:
            if self.delivery_point_id.picking_type_id:
                self.picking_type_id = self.delivery_point_id.picking_type_id

    def get_company_currency_amount(self):
        return self.currency_id._convert(self.amount_total,self.company_id.currency_id,self.company_id,datetime.now())

    def get_quotation_link(self):
        link = '/web#id=%s&action=%s&model=purchase.order&view_type=form&cids=%s&menu_id=%s'%(
            self.id,
            self.env.ref('purchase.purchase_rfq').id,
            self.company_id.id,
            self.env.ref('purchase.menu_purchase_rfq').id
        )
        return link
        
    @api.onchange('delivery_days','date_order')
    def onchange_delivery_days(self):
        if self.delivery_days and self.date_order:
            self.date_planned = self.date_order + timedelta(self.delivery_days)

    def get_delivery_partner_id(self):
        if self.delivery_point_id:
            return self.delivery_point_id
        else:
            return self.picking_type_id.warehouse_id.partner_id

    @api.depends('order_line.price_total', 'order_line.discount', 'order_line.discount_persen', 'order_line.discount', 'order_line.price_view', 'order_line.product_qty', 'discount_type', 'discount_persen')
    def _amount_all(self):
        for order in self:
            order.discount_total = 0.0
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            order.discount_total = sum(order_lines.mapped('discount'))
            order.amount_untaxed = sum(order_lines.mapped('price_subtotal'))
            order.amount_total = sum(order_lines.mapped('price_total'))
            order.amount_tax = sum(order_lines.mapped('price_tax'))

    @api.constrains('print_po_date', 'delivery_days')
    def constrains_print_po_date(self):
        for rec in self:
            if rec.print_po_date and rec.delivery_days:
                rec.date_planned = rec.print_po_date + timedelta(rec.delivery_days)

    def action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase')[2]
            else:
                template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase_done')[2]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
        except ValueError:
            compose_form_id = False
        pdf = self.env['ir.actions.report'].sudo()._render_qweb_pdf('metalindo_purchase.metalindo_action_report_vendor_acknowledge', int(self.id))
        b64_pdf = base64.b64encode(pdf[0])
        # save pdf as attachment
        templates = self.env['mail.template'].browse(template_id)
        name = "Vendor Acknowledge - %s - %s"%(self.partner_id.name or '', self.name)
        attachments = self.env['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'datas': b64_pdf,
            'store_fname': name,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        terms_and_condition = False
        syarat_ind = "metalindo_purchase/static/pdf/syarat_idn.pdf"
        syarat_eng = "metalindo_purchase/static/pdf/syarat_eng.pdf"
        if self.partner_id.code_id.impor_domestik == "domestik":
            terms_and_condition = base64.b64encode(file_open(syarat_ind, 'rb').read())
        elif self.partner_id.code_id.impor_domestik == "impor":
            terms_and_condition = base64.b64encode(file_open(syarat_eng, 'rb').read())
        attachments_term = self.env['ir.attachment'].create({
            'name': 'Terms and Condition.pdf',
            'type': 'binary',
            'datas': terms_and_condition,
            'store_fname': 'Terms and Condition.pdf',
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        templates.attachment_ids = [(6,0,[attachments.id, attachments_term.id])]
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'active_model': 'purchase.order',
            'active_id': self.ids[0],
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': "mail.mail_notification_layout_with_responsible_signature",
            'force_email': True,
            'mark_rfq_as_sent': True,
        })

        # In the case of a RFQ or a PO, we want the "View..." button in line with the state of the
        # object. Therefore, we pass the model description in the context, in the language in which
        # the template is rendered.
        lang = self.env.context.get('lang')
        if {'default_template_id', 'default_model', 'default_res_id'} <= ctx.keys():
            template = self.env['mail.template'].browse(ctx['default_template_id'])
            if template and template.lang:
                lang = template._render_lang([ctx['default_res_id']])[ctx['default_res_id']]

        self = self.with_context(lang=lang)
        if self.state in ['draft', 'sent']:
            ctx['model_description'] = _('Request for Quotation')
        else:
            ctx['model_description'] = _('Purchase Order')

        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
    
    def validation_order_line(self):
        for this in self:
             if not this.order_line:
                raise ValidationError(_('PO item cannot be empty.'))

    def check_validation(self):
        for this in self:
            if this.partner_id.state == 'draft':
                raise ValidationError('Data vendor belum lengkap, mohon di lengkapi terlebih dahulu')
            for line in this.order_line:
                if line.product_qty <= 0:
                    raise ValidationError(_('Qty cannot be empty'))
                if line.price_view <= 0:
                    raise ValidationError(_('Price cannot be empty'))

    def button_submit(self):
        self.check_validation()
        return super(purchase_order, self).button_submit()

    @api.depends('user_id')
    def _compute_current_user_is_buyer(self):
        for rec in self:
            rec.current_user_is_buyer = self.env.user == rec.user_id

    def generate_po_slip(self, po_report_filename=None):
        self.ensure_one()

        syarat_pdf = False
        report = tempfile.gettempdir()+'/report.pdf'
        syarat_id = tempfile.gettempdir()+'/syarat.pdf'
        report_po = 'purchase.action_report_purchase_order'
        syarat_ind = "metalindo_purchase/static/pdf/syarat_idn.pdf"
        syarat_eng = 'metalindo_purchase/static/pdf/syarat_eng.pdf'
        if self.partner_id.code_id.impor_domestik == "domestik":
            syarat_pdf = file_open(syarat_ind, 'rb').read()
        elif self.partner_id.code_id.impor_domestik == "impor":
            syarat_pdf = file_open(syarat_eng, 'rb').read()
        else:
            raise UserError('Vendor Code belum ada import atau domestik')
        purchase_pdf, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf(report_po, int(self.id))
        a = open(report,'wb')
        a.write(purchase_pdf)
        a.close()
        syarat = open(syarat_id, 'wb')
        syarat.write(syarat_pdf)
        syarat.close
        final = PdfFileMerger()
        final.append(report,import_bookmarks=False)
        final.append(syarat_id, import_bookmarks=False)
        final_file = tempfile.gettempdir()+'/final.pdf'
        final.write(final_file)
        final.close()
        c = open(final_file, 'rb')
        pdf = c.read()
        c.close()

        po_report = base64.b64encode(pdf)
        # Set a default value for po_report_filename if it's not defined
        if not po_report_filename:
            po_report_filename = "Purchase Order %s.pdf"%self.name
        self.write({
            'po_report': po_report,
            'po_report_filename': po_report_filename,
        })

        attachment_obj = self.env['ir.attachment'].sudo().search([
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('res_field', '=', 'po_report'),
        ])
        attachment = attachment_obj.copy()
        attachment.write({
            'res_field': None,
            'name': attachment.create_date.strftime('%Y-%m-%d ') + po_report_filename
        })

        # These return values were historically used by the controller `download_report_purchase_order()`
        # in metalindo_purchase/controllers/controllers.py. That controller is no longer there, but
        # we'll keep these here (with slight modifications) for future use.
        return {
            'po_report': po_report,
            'po_report_filename': po_report_filename
        }


class product_category(models.Model):
    _inherit = 'product.category'

    procurement_user_id = fields.Many2one('res.users','Procurement Responsible')
    analytic_id = fields.Many2one('account.analytic.account', 'Cost Center')
