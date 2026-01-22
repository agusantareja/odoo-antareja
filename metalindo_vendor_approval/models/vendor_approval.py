from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import requests
import json
import re

class ResPartnerVendorApproval(models.Model):
    _inherit = 'res.partner'

    approval_ids = fields.One2many('cni.approval.transaction', 'transaction_id', string="Approval", domain=[('form_id','=','res.partner')])
    approval_type = fields.Selection(selection_add=[
        ('registration', 'Vendor Registration'),
        ('blacklist', 'Vendor Blacklist'),
        ('whitelist', 'Vendor Whitelist'),
        ('change', 'Vendor Change'),
    ])
    approval_type_label = fields.Html(compute='_compute_approval_type_label')
    flag_reject = fields.Boolean(string="Flag Reject")
    note_reject = fields.Text(string="Note Reject")
    is_approver = fields.Boolean(compute='_compute_is_approver')
    alert_waiting_approval = fields.Text(string="Alert waiting approval", compute="compute_approver_group")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting','Waiting For Approval'),
        ('approved','Approved'),
        ('reject', 'Rejected'),
        ('blacklisted', 'Blacklisted'),
    ], default='draft', tracking=True)
    cancel_by = fields.Many2one('res.users', string="Canceled By", tracking=True)
    cancel_date = fields.Datetime(string="Canceled Date", tracking=True)
    request_blacklist_by = fields.Many2one('res.users', string="Request Blacklist By", tracking=True)
    request_blacklist_date = fields.Datetime(string="Request Blacklist Date", tracking=True)
    request_whitelist_by = fields.Many2one('res.users', string="Request Whitelist By", tracking=True)
    request_whitelist_date = fields.Datetime(string="Request Whitelist Date", tracking=True)
    blacklist_reason = fields.Text(string="Blacklist Reason", tracking=True)
    whitelist_reason = fields.Text(string="Whitelist Reason", tracking=True)
    create_uid = fields.Many2one('res.users', string="Create By", readonly=True, tracking=True)
    create_date = fields.Datetime(string="Create Date", readonly=True, tracking=True)
    request_change_by = fields.Many2one('res.users', string="Request Change By", tracking=True)
    request_change_date = fields.Datetime(string="Request Change Date", tracking=True)
    change_reason = fields.Text(string="Change Reason", tracking=True)
    change_data = fields.Json(string="Change Data")
    vendor_link = fields.Char('PR Link', compute="get_link")

    @api.depends('company_id')
    def get_link(self):
        for rec in self:
            link = '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s'%(
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                rec.id,
                rec._name,
                rec.company_id.id,
                self.env.ref('metalindo_vendor_approval.vendors_root_menu').id
            )
            rec.vendor_link = link

    def send_wa_notif(self, partner, trx):
        url = self.env['ir.config_parameter'].get_param('wa_bot.end_point')
        token = self.env['ir.config_parameter'].get_param('wa_bot_token')
        number_wa = self.env['ir.config_parameter'].get_param('wa_test_number')
        if not number_wa:
            if partner.mobile:
                number_wa = partner.mobile.replace('+','').replace('-','').replace(' ','')
            
        message = f"""
Hai {partner.name}, Vendor berikut membutuhkan approval anda

Vendor : {trx.name}

Mohon periksa pengajuan melalui link dibawah. 
{trx.vendor_link}

Terima kasih

_Pesan ini adalah pesan otomatis dari sistem ERP CMP_
        """
        data = {
            'token': token,
            'message': message,
            'recipient': number_wa,
            'ref': 'message vendor approval',
        }
        # print(data)
        # print(url)
        post_data = requests.post(url=url, json=data)
        # print(post_data)
        # print(post_data.text)

    
    
    def send_email_notif(self, partner, trx):
        email = self.env['ir.config_parameter'].get_param('test_email')
        if not email:
            if partner.email:
                email = partner.email
        # print(email)
        if email:
            template = self.env.ref('metalindo_vendor_approval.vendor_approval_mail_template')
            template_values = {
                'email_to'      : email,
                'email_cc'      : False,
                'auto_delete'   : True,
                'partner_to'    : False,
                'scheduled_date': False,
            }
            if template:
                template.sudo().write(template_values)
                with self.env.cr.savepoint():
                    mail_template = template.sudo().send_mail(trx.id, force_send=True)
    
    
    def button_request_approval(self):
        self._prevent_empty_address_fields()
        self.approval_ids = False
        self.env['cni.matrix.approval.line'].request_by_value(
            self,
            0,
            False,
            'vendor approval'
        )

        # SEND NOTIF APPROVAL WA DAN MAIL
        approval_lines_ids = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', self.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'vendor approval')], limit=1, order='seq asc')
        for user in approval_lines_ids.group_id.users:
            if user.id in [1, 2] or user.admin_user:
                continue  # skip administrators (just in case)
            self.send_email_notif(user.partner_id, self)
            self.send_wa_notif(user.partner_id, self)

        self.write({'state': 'waiting', 'flag_reject': False})

    
    def button_approve_approval(self):
        approval_sts = self.env['cni.matrix.approval.line'].approve(self)

        # SEND NOTIF APPROVAL WA DAN MAIL
        approval_lines_ids = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', self.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'vendor approval')], limit=1, order='seq asc')
        for user in approval_lines_ids.group_id.users:
            self.send_email_notif(user.partner_id, self)
            self.send_wa_notif(user.partner_id, self)
        
        
        if approval_sts == 0:
            final_state = 'blacklisted' if self.approval_type == 'blacklist' else 'approved'
            self.sudo().write({
                'state': final_state,
                'approval_type': False,
                'flag_reject': False,
                'change_data': False
            })
            # The vendor documents' states must also be updated accordingly
            if self.document_ids:
                self.document_ids.sudo().write({'state': 'approved'})

    
    def _compute_is_approver(self):
        for rec in self:
            user_id = self.env.user.id
            approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'vendor approval')], limit=1, order='seq asc')
            if user_id in approver.group_id.users.ids:
                rec.is_approver = True
            else:
                rec.is_approver = False

    def compute_approver_group(self):
        """Compute untuk alert approver"""
        for rec in self:
            approver_name = ""
            list_approver = []
            approver_user = ""
            param = self.env['ir.config_parameter'].sudo().get_param('metalindo_approval.alert_waiting_approval')
            approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', rec.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'vendor approval')], limit=1, order='seq asc')
            if approver:
                approver_name = approver.group_id.display_name
                if approver.group_id.users:
                    for user in approver.group_id.users:
                        if user.id in [1, 2] or user.admin_user:
                            continue
                        list_approver.append(user.name)
            if list_approver:
                approver_user = " / ".join(list_approver)
                approver_name = approver_name+" ( "+approver_user+" )"
            alert = param.replace("{approver}", str(approver_name))
            rec.alert_waiting_approval = alert

    def button_reject(self):
        if self.env.user.has_group('metalindo_vendor_approval.group_metalindo_vendor_approval'):
            self.write({
                'state': 'reject',
                'reject_by': self.env.uid,
                'reject_date': datetime.now(),
            })
        else:
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak menolak vendor ini."))
        return True
    
    def button_cancel(self):
        if self.env.user.has_group('metalindo_vendor_approval.group_metalindo_vendor_approval'):
            self.write({
                'state': 'waiting',
                'cancel_by': self.env.uid,
                'cancel_date': datetime.now(),
            })
        else:
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak membatalkan vendor ini."))
        return True

    def button_request_blacklist(self):
        action = self.env.ref('metalindo_vendor_approval.vendor_blacklist_wizard_action').read()[0]
        action.update({
            'context' : {'default_vendor_id': self.id},
        })
        return action

    def button_request_whitelist(self):
        action = self.env.ref('metalindo_vendor_approval.vendor_whitelist_wizard_action').read()[0]
        action.update({
            'context' : {'default_vendor_id': self.id},
        })
        return action

    def write(self, vals):
        # import pdb;pdb.set_trace()
        if vals.get('active') is False and self.state == 'approved' and not self.env.user.has_group('metalindo_vendor_approval.group_metalindo_vendor_approval'):
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak menon-aktifkan vendor ini."))
        else:
            ret_val = True # just so we can maintain the .write() method behaviour of returning a boolean
            ret_val = ret_val and super().write(vals)
            # Contact tipe individual (bukan company) tidak perlu proses approval sehingga langsung dibuat state-nya menjadi 'approved'
            non_company_records = self.filtered(lambda rec: not rec.is_company)
            ret_val = ret_val and super(__class__, non_company_records).write({'state': 'approved'})
            return ret_val

    def unlink(self):
        # import pdb;pdb.set_trace()
        for rec in self:
            if rec.state == 'approved' and not self.env.user.has_group('metalindo_vendor_approval.group_metalindo_vendor_approval'):
                raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak menghapus vendor ini."))
        res = super(ResPartnerVendorApproval, self).unlink()
        return res

    def button_request_change(self):
        action = self.env.ref('metalindo_vendor_approval.vendor_change_wizard_action').read()[0]
        action.update({
            'context' : {'default_vendor_id': self.id},
        })
        return action

    def button_approve_change(self):
        if self.env.user.has_group('metalindo_vendor_approval.group_metalindo_vendor_approval'):
            change_data = json.loads(self.change_data)
            vals = {
                'state_blacklist': False,
                'approve_change_by': self.env.uid,
                'approve_change_date': datetime.now(),
                }
            if change_data.get('name'):
                vals['name'] = change_data['name']
            if change_data.get('type'):
                if change_data['type'] == 'company':
                    vals['is_company'] = True
                else:    
                    vals['is_company'] = False
            if change_data.get('npwp'):
                vals['vat'] = change_data['npwp']
            self.write(vals)
        else:
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak mem-blacklist vendor ini."))
        return True

    def button_reject_change(self):
        if self.env.user.has_group('metalindo_vendor_approval.group_metalindo_vendor_approval'):
            self.write({
                'state_blacklist': False,
                'reject_change_by': self.env.uid,
                'reject_change_date': datetime.now(),
            })
        else:
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak menolak blacklist vendor ini."))
        return True

    # Generate a label for indicating the current approval type
    @api.depends('approval_type')
    def _compute_approval_type_label(self):
        for record in self:
            # Get the human-readable string of the approval type
            approval_type_string = dict(record._fields['approval_type'].selection).get(record.approval_type)

            # For determining which background color to use for the label
            bg_color_class = ''
            if record.approval_type == 'registration':
                bg_color_class = 'bg-info'
            elif record.approval_type == 'blacklist':
                bg_color_class = 'bg-danger'
            elif record.approval_type == 'whitelist':
                bg_color_class = 'bg-success'
            elif record.approval_type == 'change':
                bg_color_class = 'bg-secondary'

            # Generate the relevant HTML code for the label
            record.approval_type_label = f"""
                <p class="mb-0 py-1 px-3 rounded-pill {bg_color_class} text-white text-uppercase text-center">
                    {approval_type_string}
                </p>
            """

    # New non-company contacts should not have approval_type set
    @api.onchange('is_company')
    def _onchange_approval_type(self):
        if self._origin.approval_type != 'change':
            if self.is_company:
                self.approval_type = 'registration'
            else:
                self.approval_type = False

    # BEGIN: methods for handling change_data
    def _update_change_data(self, field):
        """
        A helper function to update change_data field appropriately

        :param str field: The name of the field that's just updated
        """
        if (self.state == 'draft') and (self.approval_type == 'change'):
            old_field_value = self._origin[field]
            new_field_value = self[field]
            new_change_data = self.change_data
            # In case the given field is actually a relational field
            if issubclass(old_field_value.__class__, models.Model):
                old_field_value = old_field_value.name
            if issubclass(new_field_value.__class__, models.Model):
                new_field_value = new_field_value.name
            if not new_change_data:                
                new_change_data = {field: [old_field_value, new_field_value]}
            elif field in new_change_data:
                new_change_data[field][1] = new_field_value
            else:
                new_change_data[field] = [old_field_value, new_field_value]
            self.change_data = new_change_data

    # TODO: this needs further troubleshooting (for some reason, the name change is not saved, even
    #       though self.change_data has been correctly set at the end of this onchange function).
    #@api.onchange('name')
    #def _update_change_data_name(self):
    #    self._update_change_data('name')

    @api.onchange('street')
    def _update_change_data_street(self):
        self._update_change_data('street')

    @api.onchange('street2')
    def _update_change_data_street2(self):
        self._update_change_data('street2')

    @api.onchange('city')
    def _update_change_data_city(self):
        self._update_change_data('city')

    @api.onchange('state_id')
    def _update_change_data_state_id(self):
        self._update_change_data('state_id')

    @api.onchange('zip')
    def _update_change_data_zip(self):
        self._update_change_data('zip')

    @api.onchange('country_id')
    def _update_change_data_country_id(self):
        self._update_change_data('country_id')

    @api.onchange('phone')
    def _update_change_data_phone(self):
        self._update_change_data('phone')

    @api.onchange('mobile')
    def _update_change_data_mobile(self):
        self._update_change_data('mobile')

    @api.onchange('email')
    def _update_change_data_email(self):
        self._update_change_data('email')

    @api.onchange('website')
    def _update_change_data_website(self):
        if self.website and (not re.search("^https?://", self.website)):
            self.website = 'http://' + self.website
        self._update_change_data('website')
    # END: methods for handling change_data

    def reject_approval_wizard_action(self):
        if self.purchase_order_count > 0:
            raise ValidationError(_("You cannot reject this vendor because already have a purchase order transaction."))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Vendor',
            'res_model': 'cni.reject.approval',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'model_name': 'res.partner',
                'default_res_id': self.id,
                'update_value': {'state': 'draft'}
            }
        }

    def _compute_supplier_selectable(self):
        super(ResPartnerVendorApproval,self)._compute_supplier_selectable()
        for record in self.filtered( lambda  r: r.supplier_selectable and record.state != 'approved'):
            record.supplier_selectable = False

    def _search_supplier_selectable(self, operator, value):
        if operator not in ['=', '!='] or value not in [True, False]:
            raise UserError(_("Invalid domain for supplier_select_able field"))
        domain = super(ResPartnerVendorApproval,self)._search_supplier_selectable(operator, value)
        if ((operator == '=') and (value is True)) or ((operator == '!=') and (value is False)):
            return domain + [('state', '=', 'approved')]
        else:
            return ['|'] + domain + [('state', '!=', 'approved')]

    def _compute_supplier_readonly(self):
        for record in self:
            record.supplier_readonly = record.supplier_rank > 0 and record.state == 'approved'

    def _compute_website_readonly(self):
        super(ResPartnerVendorApproval, self)._compute_website_readonly()
        for rec in self.filtered(lambda r : r.supplier_rank > 0 and not r.website_readonly and r.state == 'approved'):
            rec.website_readonly = True

    def _compute_category_id_readonly(self):
        super(ResPartnerVendorApproval, self)._compute_category_id_readonly()
        for rec in self.filtered(lambda r : r.supplier_rank > 0 and not r.category_id_readonly and r.state != 'approved'):
            rec.category_id_readonly = True

    def _compute_l10n_id_pkp_readonly(self):
        super(ResPartnerVendorApproval, self)._compute_l10n_id_pkp_readonly()
        for rec in self.filtered(lambda r : r.supplier_rank > 0 and not r.website_readonly and r.state != 'draft'):
            rec.l10n_id_pkp_readonly = True
