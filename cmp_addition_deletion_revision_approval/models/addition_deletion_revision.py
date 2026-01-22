# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import re


class AdditionDeletionRevision(models.Model):
    _inherit = 'addition.deletion.revision'

    link = fields.Char(copy=False)
    approval_ids = fields.One2many('cni.approval.transaction', 'transaction_id', string="Approval", domain=[('form_id','=','addition.deletion.revision')])
    is_sent_email_approval = fields.Boolean(default=False)
    email_penerima_approval = fields.Char('Email Penerima')
    adr_status = fields.Selection(selection_add=[('waiting','Waiting For Approval'), ('approved',)], copy=False)
    is_approver = fields.Boolean(compute='_compute_is_approver')
    todo = fields.Boolean(string='To Do', compute=True, search='_filter_todo')
    alert_waiting_approval = fields.Text(string='Alert waiting approval', compute='compute_approver_group')
    flag_reject = fields.Boolean(string='Flag Reject', default=False)
    note_reject = fields.Text(string='Note Reject')
    alert_waiting_finalized = fields.Text(string='Alert waiting finalized', compute='compute_finalized')
    alert_waiting_hs_code = fields.Text(string='Alert waiting hs code', compute='compute_hs_code')
    can_edit = fields.Boolean(string='Can Edit', compute='compute_can_edit')
    mandatory = fields.Boolean(string='Mandatory', compute='compute_mandatory')
    approval_group_status = fields.Char(string='Approval Group Status', compute='_compute_approval_group_status', store=True)
    line_readonly = fields.Boolean(compute='_compute_line_readonly')
    spv_cataloger_approved = fields.Boolean(compute='_compute_spv_cataloger_approved')
    warning_information = fields.Html(compute='set_warning_information')

    def warning_information_preview(self):
        self.ensure_one()
        return {
            'name': _('Warning Information'),
            'type': 'ir.actions.act_window',
            'res_model': 'addition.deletion.revision',
            'res_id': self.id,
            'target': 'new',
            'views': [(self.env.ref('cmp_addition_deletion_revision_approval.cmp_warning_information_addition_deletion_revision_form').id, 'form')],
        }

    @api.depends('line_ids.product_template_id')
    def set_warning_information(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        menu_id = self.env.ref('stock.menu_stock_root').id
        action_id = self.env.ref('stock.product_template_action_product').id

        def _render_links(product_templates):
            if not product_templates:
                return ""
            return "".join(
                "<p style='margin:0;'>- <a href='{url}' target='_blank'>{name}</a></p>".format(
                    url="%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s&action=%s" % (
                        base_url,
                        pt.id,
                        pt._name,
                        self.env.company.id,
                        menu_id,
                        action_id,
                    ),
                    name=pt.display_name,
                )
                for pt in product_templates
            )

        for this in self:
            this.warning_information = False
            product_templates = this.line_ids.product_template_id
            if not product_templates:
                continue
            this.warning_information = (
                "<p style='margin:0;'>The stock item:</p>"
                f"{_render_links(product_templates)}"
                "<p style='margin:0;'>will be automatically updated according to the changes that have been made.</p>"
            )

    @api.depends_context('uid')
    @api.depends('adr_status', 'spv_cataloger_approved')
    def _compute_line_readonly(self):
        for rec in self:
            rec.line_readonly = not (
                rec.adr_status == 'draft'
                or (rec.adr_status == 'waiting' and not rec.spv_cataloger_approved)
            )

    @api.depends('approval_ids.group_id', 'approval_ids.sts')
    def _compute_spv_cataloger_approved(self):
        spv_cataloguer_group = self.env.ref('metalindo_inventory.group_metalindo_inventory_spv_cataloguer')
        for rec in self:
            rec.spv_cataloger_approved = bool(
                rec.approval_ids.filtered_domain([('group_id', '=', spv_cataloguer_group.id), ('sts', '=', '2')])
            )

    @api.depends('approval_ids', 'approval_ids.sts')
    def _compute_approval_group_status(self):
        # Preload adr_status selection labels once for efficiency
        field_info = self.fields_get(['adr_status'], ['selection'])
        selection_map = dict(field_info['adr_status']['selection'])

        for rec in self:
            if rec.adr_status == 'waiting':
                pending_approvers = rec.approval_ids.filtered_domain([('sts', '=', '1')]).sorted(key='seq')
                if pending_approvers:
                    rec.approval_group_status = pending_approvers[0].group_id.display_name
                    continue

            # Fallback: use the human-readable adr_status label
            rec.approval_group_status = selection_map[rec.adr_status]

    def compute_can_edit(self):
        for rec in self:
            rec.can_edit = False
            approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'addition deletion revision')], limit=1, order='id asc')
            if approver and approver.can_edit:
                rec.can_edit = True
    
    def compute_mandatory(self):
        for rec in self:
            rec.mandatory = False
            approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'addition deletion revision')], limit=1, order='id asc')
            if approver and approver.mandatory:
                rec.mandatory = True

    def _compute_is_approver(self):
        for rec in self:
            user_id = self.env.user.id
            approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'addition deletion revision')], limit=1, order='seq asc')
            if user_id in approver.group_id.users.ids:
                rec.is_approver = True
            else:
                rec.is_approver = False

    def send_notif_wa(self, approvers):
        for user in approvers[0].group_id.users:
            if self.analytic_id not in user.sudo().account_analytic_ids:
                continue
            if user.id in [1, 2] or user.admin_user:
                continue 
            self.send_notif_approver(user)

    def button_request_approval(self):
        self.approval_ids = False
        self.env['cni.matrix.approval.line'].request_by_value(self, self.total_value, self.currency_id, 'addition deletion revision')
        self.write({
            'adr_status':'waiting', 
            'flag_reject': False
        })
        approvers = self.approval_ids.filtered_domain([('sts', 'in', ['1', '3'])]).sorted(key='seq')
        if approvers:
            self.send_notif_wa(approvers)

    def ready_for_spv_cataloger_approval(self, approval_transactions):
        self.ensure_one()
        next_approval = approval_transactions[0] if approval_transactions else self.env['cni.approval.transaction']
        inventory_spv_cataloguer = self.env.ref('metalindo_inventory.group_metalindo_inventory_spv_cataloguer')

        return bool(
            next_approval.group_id == inventory_spv_cataloguer
            and self.line_ids.product_template_id
        )

    def button_approve_approval(self):
        approval_transactions = self.approval_ids.filtered_domain([('sts', '!=', '2')]).sorted(key='seq')
        ready_for_spv_cataloger_approval = self.ready_for_spv_cataloger_approval(approval_transactions)
        if ready_for_spv_cataloger_approval and not self.env.context.get('action'):
            return self.warning_information_preview()

        self.event_before_approve(approval_transactions)
        approval_sts = self.env['cni.matrix.approval.line'].approve(self)
        self.update({'flag_reject': False})
        if approval_sts == 0:
            self.write({
                'approved_by': self.approved_by or self.env.uid,
                'approved_date': self.approved_date or fields.Date.context_today(self),
                'done_by': None,
                'done_date': None,
                'adr_status': 'done'
            })
        approvers = self.approval_ids.filtered_domain([('sts', 'in', ['1', '3'])]).sorted(key='seq')
        if approvers:
           self.send_notif_wa(approvers)

        return True

    def event_before_approve(self, approval_transactions=None):
        self.check_mandatory()
        # FINALIZE CATALOGER
        trx = self.ensure_one()
        next_approval = approval_transactions[0] if approval_transactions else self.env['cni.approval.transaction']
        inventory_cataloger = self.env.ref('metalindo_inventory.group_metalindo_inventory_cataloger')
        if next_approval.group_id == inventory_cataloger:
            if trx.req_type != 'del':
                trx.write({
                    'finalized_by': self.env.uid,
                    'finalized_date': fields.Date.context_today(self),
                })
            else:
                trx.write({
                    'done_by': self.env.uid,
                    'done_date': fields.Date.context_today(self),
                })

        # SPV CATALOGER STOCK ITEM
        inventory_spv_cataloguer = self.env.ref('metalindo_inventory.group_metalindo_inventory_spv_cataloguer')
        if next_approval.group_id == inventory_spv_cataloguer:
            trx.sudo()._add_del_rev()

        # OFFICER EXIM INPUT HSCODE
        officer_exim = self.env.ref('metalindo_inventory.group_metalindo_officer_exim')
        if next_approval.group_id == officer_exim:
            for line in trx.line_ids:
                if not line.product_hscode_id:
                    raise ValidationError('HS Code "%s" harus diisi!' % (line.name or line.standard_name))
                line.product_template_id.sudo().write({
                    'product_hscode_id': line.product_hscode_id.id,
                })
            trx.write({
                'done_by': self.env.uid,
                'done_date': fields.Date.context_today(self),
            })

    def _format_phone_number(self, phone):
        if not phone:
            return False
        
        phone = re.sub(r'\D', '', phone)
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif not phone.startswith('62'):
            phone = '62' + phone

        return phone

    def send_notif_approver(self, user):
        self.ensure_one()
        phone = user.partner_id.mobile or user.partner_id.phone
        phone = self._format_phone_number(phone)
        template = self.env.ref('cmp_addition_deletion_revision_approval.whatsapp_template_adr', raise_if_not_found=False)
        if template and phone:
            self.with_context(recipients=user.partner_id, phone=phone)\
                .send_whatsapp_by_template(template.name)
            
    def _filter_todo(self, operator, value):
        """Search untuk user yang belum approve"""
        ids = []
        is_cataloger = self.user_has_groups('metalindo_inventory.group_metalindo_inventory_cataloger')
        inventory_cataloger = self.env.ref('metalindo_inventory.group_metalindo_inventory_cataloger')
        
        is_spv_cataloguer = self.user_has_groups('metalindo_inventory.group_metalindo_inventory_spv_cataloguer')
        inventory_spv_cataloguer = self.env.ref('metalindo_inventory.group_metalindo_inventory_spv_cataloguer')
        
        is_officer_exim = self.user_has_groups('metalindo_inventory.group_metalindo_officer_exim')
        inventory_officer_exim = self.env.ref('metalindo_inventory.group_metalindo_officer_exim')
        
        adrs = self.env['addition.deletion.revision'].sudo().search([('adr_status', '!=', 'done')])
        for adr in adrs:
            approvals = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', adr.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'addition deletion revision')], limit=1, order='seq asc')
            if is_cataloger or is_spv_cataloguer or is_officer_exim:
                if self._uid in approvals.group_id.users.ids:
                    if approvals.group_id == inventory_cataloger:
                        ids.append(approvals.transaction_id)
                    elif approvals.group_id == inventory_spv_cataloguer:
                        ids.append(approvals.transaction_id)
                    elif approvals.group_id == inventory_officer_exim:
                        ids.append(approvals.transaction_id)
            else:
                ids.append(adr.id)
        return [('id', 'in', ids)]

    def compute_approver_group(self):
        """Compute untuk alert approver"""
        for rec in self:
            approver_name = ""
            list_approver = []
            approver_user = ""
            param = self.env['ir.config_parameter'].sudo().get_param('metalindo_approval.alert_waiting_approval')
            approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'addition deletion revision')], limit=1, order='id asc')
            if approver:
                approver_name = approver.group_id.display_name
                if approver.group_id.users:
                    for user in approver.group_id.users:
                        if user.id in [1, 2] or user.admin_user:
                            continue
                        if (not approver.skip_cost_center_check) and (rec.analytic_id.id not in user.account_analytic_ids.ids):
                            continue
                        list_approver.append(user.name)
            if list_approver:
                approver_user = " / ".join(list_approver)
                approver_name = approver_name+" ( "+approver_user+" ) "
            alert = param.replace("{approver}", str(approver_name))
            rec.alert_waiting_approval = alert
            
    def compute_finalized(self):
        """compute untuk memunculkan informasi untuk menunggu finalized dari cataloger"""
        for rec in self:
            param = self.env['ir.config_parameter'].sudo().get_param('metalindo_approval.alert_waiting_finalized')
            if rec.adr_status == 'approved':
                rec.alert_waiting_finalized = param
            else:
                rec.alert_waiting_finalized = False
                
    def compute_hs_code(self):
        for rec in self:
            param = self.env['ir.config_parameter'].sudo().get_param('metalindo_approval.alert_waiting_hs_code')
            if rec.adr_status == 'final':
                rec.alert_waiting_hs_code = param
            else:
                rec.alert_waiting_hs_code = False

    def check_mandatory(self):
        for rec in self:
            if rec.mandatory:
                for line in rec.line_ids:
                    if not line.name:
                        raise UserError('Short Description "%s" harus diisi!'%(line.name or line.standard_name))
                    if not line.product_desc:
                        raise UserError('Long Description "%s" harus diisi!'%(line.name or line.standard_name))
                    
    def get_link(self):
        for rec in self.filtered_domain([('link', '=', False)]):
            rec.link = '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s'%(
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                self.id,
                self._name,
                self.company_id.id,
                self.env.ref('metalindo_inventory.menu_metalindo_addition_deletion_revision').id
            )

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AdditionDeletionRevision, self).create(vals_list)
        res.get_link()
        return res
    
    def write(self, vals):
        res = super(AdditionDeletionRevision, self).write(vals)
        self.get_link()
        return res


class AdditionDeletionRevisionLine(models.Model):
    _inherit = 'addition.deletion.revision.line'

    
    mandatory = fields.Boolean(string='Mandatory', related='adr_id.mandatory')
