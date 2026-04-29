# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class recommend_qty(models.Model):
    _name = "recommend.qty"
    _order = 'name desc'

    name = fields.Char(string="RO Number", readonly=True, copy=False, index=True, default=lambda self: _('New'))
    product_id = fields.Many2one('product.product','Product')
    #product_criticality_id readonly false karena takut sewaktu waktu buyer bisa merubah rubah, jadi readonlynya dipasang di xml
    product_criticality_id = fields.Many2one('product.criticality', 'Criticality Area', related='product_id.product_criticality_id', store=True, readonly=False)
    product_desc = fields.Text('Product Description',compute="get_product_desc")
    recommend_qty = fields.Integer('Recommended Quantity')
    state = fields.Selection([
        ('Draft','Draft'),
        ('Assignment', 'Assignment'),
        ('Ready to Purchase','Ready to Purchase'),
        ('On Tender', 'On Tender'),
        ('In Procurement','On Purchase'),
        ('Done','Done'),
    ],string='Status',default="Draft")
    categ_group_allowed = fields.Boolean('Group Allowed',search="search_allowed_product",compute=True)
    purchase_qty = fields.Integer('SRO Qty') #ini tadinya digunakan untuk SRO dan BRO skrng di split
    bro_purchase_qty = fields.Integer('BRO Qty')
    note = fields.Char('Note')
    product_min_qty = fields.Float(string="Reordering Point")
    product_max_qty = fields.Float(string="Reordering Quantity")
    company_id = fields.Many2one('res.company','Company')
    recommend_date = fields.Datetime('Recommended on')
    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint','Order Point')
    procurement_user_id = fields.Many2one('res.users','Buyer', 
        default=lambda self: self.product_id.categ_id.procurement_user_id,
        domain=lambda self: [('groups_id', 'in', [u.group_id.id for u in self.env['cni.matrix.approval.line'].sudo().search([(
            'approval_id', '=', self.env.ref('metalindo_approval.matrix_approval_purchase_order').id)])])]
        )
    default_procurement_user_id = fields.Many2one('res.users','Buyer',related="product_id.categ_id.procurement_user_id")
    purchase_id = fields.Many2one('purchase.order', string='PO Number')
    requisition_id = fields.Many2one('purchase.requisition')
    procurement_ref = fields.Char('Reference',compute="get_procurement")
    qty_available = fields.Float('On Hand')
    qty_received = fields.Float()
    qty_done = fields.Float('Qty After Purchase')
    reserved_qty = fields.Float('Reserved Qty')

    #SRO REPORT
    create_date = fields.Datetime('SRO Date', readonly=True)
    sro_qty = fields.Integer(compute='compute_purchase_qty', store=True, string='SRO Quantity')
    stock_code = fields.Char(related='product_id.default_code', store=True, string='Stock Code')
    material_short_description = fields.Char(related='product_id.name', store=True)
    material_long_description = fields.Text(related='product_id.description', store=True)
    manufacturer_id = fields.Many2one('res.partner', string='Manufacture / Brand', related='product_id.manufacturer_id', store=True)
    part_number = fields.Char(related='product_id.part_number', store=True, string='Part Number')
    uom_id = fields.Many2one('uom.uom', string='UoM', related='product_id.uom_id', store=True)
    approval_user_id = fields.Many2one('res.users', string='Reviewed By')
    po_date = fields.Datetime(string='PO Date', related='purchase_id.create_date', store=True)
    bro_qty = fields.Float(string='BRO Ongoing')
    bro_ref_number = fields.Char(string='Ongoing BRO number')
    po_qty = fields.Float(string='PO Ongoing')
    po_ref_number = fields.Char(string='Ongoing PO number')
    
    purchase_ids = fields.Many2many('purchase.order', string='PO Numbers', compute='get_procurement')
    purchase_order_qty = fields.Float(string='Purchase Order Qty', compute='get_procurement')
    outstanding_qty = fields.Float(string='Outstanding Qty', compute='get_procurement')
    real_purchase_order_qty = fields.Float(string='Real Purchase Order Qty', compute='get_procurement')
    active = fields.Boolean(default=True)

    @api.constrains('active')
    def _check_cannot_archive_processed_bro(self):
        bro_names = []
        for rec in self:
            if not rec.active and rec.state in ('On Tender', 'In Procurement', 'Done'):
                bro_names.append(rec.name)

        if bro_names:
            raise UserError(_('BRO %s with status On Tender, On Purchase or Done cannot be archived.') % ', '.join(bro_names))

    @api.model
    def _can_archive_current_context(self):
        if self.env.context.get('sro'):
            return self.env.user.has_group('metalindo_inventory.group_metalindo_spv_inventory')
        if self.env.context.get('bro'):
            return self.env.user.has_group('metalindo_approval.group_metalindo_scm_superintendent')
        return True

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields_meta = super().fields_get(allfields=allfields, attributes=attributes)
        if not self._can_archive_current_context():
            # WARNING: since we remove the 'active' field here, including it in the view will trigger an error.
            fields_meta.pop('active', None)
        return fields_meta

    @api.constrains('note', 'purchase_qty')
    def _check_archived_sro_not_editable(self):
        for rec in self:
            if rec.state == 'Draft' and not rec.active:
                raise UserError(_('Archived SRO cannot be updated.'))

    @api.constrains('bro_purchase_qty')
    def _check_archived_bro_not_editable(self):
        for rec in self:
            if rec.state in ('Assignment', 'Ready to Purchase') and not rec.active:
                raise UserError(_('Archived BRO cannot be updated.'))

    def get_procurement(self):
        pol = self.env['purchase.order.line']
        rq  = self.env['recommend.qty']

        for this in self:
            domain_common = [
                ('state', '!=', 'cancel'),
                ('order_id.is_rfq_tender', '=', False),
                ('product_id', '=', this.product_id.id)]
            po_lines = pol.search(domain_common + [
                '|',
                ('recommend_qty_id', '=', this.id),
                ('recommend_qty_ids', 'in', [this.id])])

            names = [this.requisition_id.display_name] if this.requisition_id else []
            names = set(names + po_lines.order_id.mapped('display_name'))
            this.purchase_ids = po_lines.mapped('order_id').ids
            this.procurement_ref = ', '.join(names) or False
            this.real_purchase_order_qty = sum(po_lines.mapped('product_qty'))

            if this.requisition_id:
                req_lines = this.requisition_id.line_ids.filtered_domain([
                    ('product_id', '=', this.product_id.id),
                    ('recommend_qty_ids', 'in', [this.id])])

                total_req_qty = float(sum(req_lines.mapped('product_qty')) or 0.0)
                if not total_req_qty:
                    this.purchase_order_qty = 0.0
                    this.outstanding_qty = float(this.bro_purchase_qty or 0.0)
                    continue

                sib_ids = set(req_lines.recommend_qty_ids.ids)
                siblings = rq.browse(sib_ids).filtered(lambda r: r.product_id == this.product_id)
                siblings = siblings.sorted(lambda r: (r.create_date, r.id))

                prior_need = 0.0
                for s in siblings:
                    if s.id == this.id:
                        break
                    prior_need += float(s.bro_purchase_qty or 0.0)

                allocated = max(0.0, min(float(this.bro_purchase_qty or 0.0), total_req_qty - prior_need))

                this.purchase_order_qty = allocated
                this.outstanding_qty    = max(float(this.bro_purchase_qty or 0.0) - allocated, 0.0)
                continue

            total_po_qty = float(sum(po_lines.mapped('product_qty')) or 0.0)
            sib_ids = set(po_lines.recommend_qty_id.ids + po_lines.recommend_qty_ids.ids)
            siblings = rq.browse(sib_ids).filtered(lambda r: r.product_id == this.product_id)
            siblings = siblings.sorted(lambda r: (r.create_date, r.id))

            prior_need = 0.0
            for s in siblings:
                if s.id == this.id:
                    break
                prior_need += float(s.bro_purchase_qty or 0.0)

            allocated = max(0.0, min(float(this.bro_purchase_qty or 0.0), total_po_qty - prior_need))
            this.purchase_order_qty = allocated
            this.outstanding_qty = max(float(this.bro_purchase_qty or 0.0) - allocated, 0.0)

    @api.depends('purchase_qty')
    def compute_purchase_qty(self):
        for this in self:
            this.sro_qty = this.purchase_qty

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                find_dcr = True
                while find_dcr:
                    vals['name'] = self.env['ir.sequence'].next_by_code('recommend.qty') or _('New')
                    find_dcr = self.env['recommend.qty'].search([('name', '=', vals['name'])], limit=1)
        return super(recommend_qty, self).create(vals_list)

    def show_procurement(self):
        self.ensure_one()
        action = {
            'name' : _(self.procurement_ref or 'Related Procurements'),
        }
        if self.purchase_id:
            view_id = self.env.ref('purchase.purchase_order_form').id
            action.update({
                'views': [[view_id, 'form']],
                'res_model' : 'purchase.order',
                'res_id' : self.purchase_id.id,
            })
            
        else:
            view_id = self.env.ref('purchase_requisition.view_purchase_requisition_form').id
            action.update({
                'views': [[view_id, 'form']],
                'res_model' : 'purchase.requisition',
                'res_id' : self.requisition_id.id,
            })
        action.update({
            'type': 'ir.actions.act_window',
            'target': 'current',
            'view_mode': 'form',
        })
        return action

    def search_allowed_product(self,operator,operand):
        if self.env.user.id in [1,2]:
            return []
        query = """
        select
        a.id
        from product_product a
        left join product_template b on a.product_tmpl_id = b.id
        left join res_group_product_category_rel c on b.categ_id = c.product_categ_id
        left join res_groups_users_rel d on d.gid = c.group_id
        where d.uid = %s
        """%self.env.user.id
        self.env.cr.execute(query)
        product_ids = [x[0] for x in self.env.cr.fetchall()]
        return [('id','in',product_ids)]
            
    @api.depends('product_id')
    def get_product_desc(self):
        for rec in self:
            desc = rec.product_id.display_name
            product_desc = rec.product_id.description 
            if product_desc:
                desc += '\n%s'%product_desc
            rec.product_desc = desc

    def approve_to_purchase(self):
        if self.filtered(lambda r: not r.active):
            raise UserError(_('Archived SRO cannot be approved.'))
        if self.purchase_qty <= 0:
            raise UserError('Value SRO cannot be empty')
        if self.procurement_ref:
            raise UserError("Product %s is already in %s"%(self.display_name,self.procurement_ref))
        self.write({
            'approval_user_id': self.env.user.id,
            'state' : 'Assignment',
            'bro_purchase_qty': self.purchase_qty
        })

    def action_create_procurement_recommend_qty(self):
        msg_null = self.filtered(lambda r: r.bro_purchase_qty <= 0)
        msg_done = self.filtered(lambda r: r.state == 'Done')
        msg_tender = self.filtered(lambda r: r.requisition_id) - msg_done
        msg_ongoing = self.filtered(lambda r: not r.requisition_id and r.outstanding_qty <= 0) - msg_done
        msg_archived = self.filtered(lambda r: not r.active)
        messages = []
        if msg_null:
            messages.append(_('BRO quantity cannot be empty in BRO number %s!') % ', '.join(msg_null.mapped('name')))
        if msg_done:
            messages.append(_('%s has been done.') % ', '.join(msg_done.mapped('name')))
        if msg_tender:
            messages.append(_('%s is currently on tender.') % ', '.join(msg_tender.mapped('name')))
        if msg_ongoing:
            messages.append(_('BRO %s is currently on going process.') % ', '.join(msg_ongoing.mapped('name')))
        if msg_archived:
            messages.append(_('Archived BRO %s cannot be processed.') % ', '.join(msg_archived.mapped('name')))
        if messages:
            raise UserError('\n'.join(messages))

        return {
            'name': _('Create Procurement'),
            'type': 'ir.actions.act_window',
            'res_model': 'create.purchase.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'recommend.qty',
                'active_ids': self.ids,
            },
        }
    
    def action_assign_buyer(self):
        list_bro = []
        for this in self:
            if this.procurement_user_id:
                raise UserError(_('Buyer has been assigned to BRO no. %s', this.name))
            if this.state == 'Done':
                raise UserError(_('Document BRO %s is already done.', this.name))
            if not this.active:
                raise UserError(_('Archived BRO %s cannot be assigned.', this.name))
            list_bro.append(this.id)
        return {
            'name': 'Buyer Assignment',
            'view_type': 'form',
            'res_model': 'metalindo_direct_charge.assign_buyer',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'target' : 'new',
            'context': {
                'default_bro_ids' : list_bro,
            }
        }
