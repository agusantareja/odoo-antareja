# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.phone_validation.tools import phone_validation
import re
import phonenumbers

class MetalindoResPartner(models.Model):
    _inherit = "res.partner"
    _order = "name, id"
    _rec_names_search = ['name', 'email', 'ref', 'vat', 'company_registry']  # TODO vat must be sanitized the same way for storing/searching

    vendor_code = fields.Char(string='Vendor Code', readonly=True, copy=False, default=lambda self: _('New'))
    code_id = fields.Many2one('vendor.code', string='Location', index=True)
    nib = fields.Char(string='NIB')
    state = fields.Selection([
        ('waiting','Waiting For Approval'),
        ('approved','Approved'),
        ('reject', 'Rejected'),
        ('blacklist', 'Blacklist'),
    ], default='waiting', tracking=True)
    create_uid = fields.Many2one('res.users', string="Create By", readonly=True)
    create_date = fields.Datetime(string="Create Date", readonly=True)
    # same_vat_partner_id = fields.Many2one('res.partner', string='Partner with same Tax ID', compute='_compute_same_vat_partner_id', store=False)
    tkdn = fields.Selection([("self_assessment","Self Assessment"),("certificate","Certificate")], string='Jenis TKDN')
    tkdn_persen = fields.Float('Persentase TKDN')
    country_id = fields.Many2one(default=lambda self: self.env.ref('base.id').id)
    document_ids = fields.One2many(comodel_name='vendor.document', inverse_name='vendor_id', string='Documents')
    code = fields.Char(string='Code')
    is_supplier = fields.Boolean(
        compute="_compute_is_supplier",
        search="_search_supplier"
    )

    supplier_selectable = fields.Boolean(
        compute="_compute_supplier_selectable",
        search="_search_supplier_selectable"
    )
    supplier_readonly = fields.Boolean(
        compute='_compute_supplier_readonly',
        help="""Readonly untuk field khusus vendor (supplier) """
    )
    supplier_blacklisted = fields.Boolean(
        store = False,
        help="""Readonly untuk field khusus vendor (supplier) """
    )

    def _compute_is_supplier(self):
        # Tidak akan overide metalindo_vendor_approval
        for record in self:
            record.supplier_selectable = record.is_company and record.supplier_rank>0

    def _search_supplier(self, operator, value):
        # Tidak akan overide metalindo_vendor_approval
        if operator not in ['=', '!='] or value not in [True, False]:
            raise UserError(_("Invalid domain for is_supplier field"))
        if ((operator == '=') and (value is True)) or ((operator == '!=') and (value is False)):
            return [('is_company', '=', True), ('supplier_rank', '>', 0), ]
        else:
            return ['|', ('is_company', '=', False), ('supplier_rank', '=', 0)]

    def _compute_supplier_selectable(self):
        # Akan di overide di module metalindo_vendor_approval
        for record in self:
            record.supplier_selectable = record.is_company and record.supplier_rank>0

    def _search_supplier_selectable(self, operator, value):
        # Akan di overide di module metalindo_vendor_approval
        if operator not in ['=', '!='] or value not in [True, False]:
            raise UserError(_("Invalid domain for supplier_select_able field"))
        if ((operator == '=') and (value is True)) or ((operator == '!=') and (value is False)):
            return [('is_company', '=', True), ('supplier_rank', '>', 0), ]
        else:
            return ['|', ('is_company', '=', False), ('supplier_rank', '=', 0)]

    def _compute_supplier_readonly(self):
        for record in self:
            record.supplier_readonly = record.supplier_rank == 0

    @staticmethod
    def _onchange_uppercase_field(record, field_name):
        # Make sure the requested field is not empty before uppercasing them
        if record[field_name]:
            record[field_name] = record[field_name].upper()

    # @api.depends('vat')
    # def _compute_same_vat_partner_id(self):
    #     for partner in self:
    #         # use _origin to deal with onchange()
    #         partner_id = partner._origin.id
    #         domain = [('vat', '=', partner.vat)]
    #         if partner_id:
    #             domain += [('id', '!=', partner_id), '!', ('id', 'child_of', partner_id)]
    #         partner.same_vat_partner_id = bool(partner.vat) and not partner.parent_id and self.env['res.partner'].search(domain, limit=1)

    def _set_vendor_code(self, vals):
        # import pdb; pdb.set_trace()
        if (vals.get('vendor_code', _('New')) == _('New') and vals.get('code_id')) or vals.get('code_id'):
            prefix = self.env['vendor.code'].search([('id', '=', vals['code_id'])], limit=1)
            find_code = True
            same_code = False
            while find_code:
                if self.vendor_code and not same_code and self.vendor_code != _('New'):
                    vc_seq = self.env['ir.sequence'].search([('code', '=', 'vendor.code')], limit=1)
                    vals['vendor_code'] = (prefix.code or '-') + self.vendor_code[(len(self.vendor_code) - vc_seq.padding):]
                    same_code = self.env['res.partner'].search([('vendor_code', '=', vals['vendor_code'])], limit=1)
                else:
                    vals['vendor_code'] = ((prefix.code or '-') + self.env['ir.sequence'].next_by_code('vendor.code')) or _('New')
                find_code = self.env['res.partner'].search([('vendor_code', '=', vals['vendor_code'])], limit=1)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # import pdb; pdb.set_trace()
            vals = self._set_vendor_code(vals)
        return super(MetalindoResPartner, self).create(vals_list)

    def write(self, vals):
        result = super(MetalindoResPartner, self).write(self._set_vendor_code(vals))
        return result

    
    # @api.depends('is_company', 'name', 'code', 'parent_id.display_name', 'type', 'company_name')
    # @api.depends_context('display_drop_point')
    # def _compute_display_name(self):
    #     # retrieve name_get() without any fancy feature
    #     print("="*50+"CONTEXT"+"="*50)
    #     print(self._context)
    #     # names = dict(self.with_context(self._context).name_get())
    #     names = dict(self.with_context({}).name_get())
    #     for partner in self:
    #         partner.display_name = names.get(partner.id)

    def name_get(self):
        names = dict(super().name_get())
        for partner in self:
            if partner.vendor_code and (partner.vendor_code != _('New')):
                names[partner.id] = '[%s] %s' % (partner.vendor_code, partner.name)
        return list(names.items())

    # Prevent empty address fields
    # @api.constrains(
    #     'vat',
    #     'email',
    #     'code_id',
    #     'street',
    #     'city',
    #     'city_id',
    #     'state_id',
    #     'zip',
    #     'country_id',
    #     'supplier_rank',
    #     'company_type',
    #     'is_company'
    # )
    def _prevent_empty_address_fields(self):
        for record in self:
            # if (record['company_type'] == 'company' or record['is_company']) and (record['supplier_rank'] > 0):
            #     is_cataloger = self.user_has_groups('metalindo_inventory.group_metalindo_inventory_cataloger') or self.user_has_groups('metalindo_inventory.group_metalindo_inventory_spv_cataloguer')
            #     if not is_cataloger:
            list_warning = ""
            
            if not record['vat']:
                list_warning += 'Kolom "NPWP" harus diisi! \n'
            if not record['email']:
                list_warning += 'Kolom "Email" harus diisi! \n'
            if not record['code_id']:
                list_warning += 'Kolom "Location" harus diisi! \n'
            if not record['street']:
                list_warning += 'Kolom "Street..." harus diisi! \n'
            if (not record['city']) and (not record['city_id']):
                list_warning += 'Kolom "City" harus diisi! \n'
            if not record['state_id']:
                list_warning += 'Kolom "State" harus diisi! \n'
            if not record['zip']:
                list_warning += 'Kolom "ZIP" harus diisi! \n'
            if not record['country_id']:
                list_warning += 'Kolom "Country" harus diisi! \n'
            
            if list_warning:
                raise ValidationError(list_warning)
    
    # Mengeset city_id akan mengubah juga nilai zip (dari modul res_partner) menjadi nilainya
    # zipcode (dari modul res_city). Karena dalam satu kota di Indonesia bisa terdapat lebih
    # dari satu nilai zip, maka sebaiknya kita matikan fitur ini kalau country_id-nya Indonesia
    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.country_id == self.env.ref('base.id'):
            if self.city_id:
                self.city = self.city_id.name
                self.state_id = self.city_id.state_id
            elif self._origin:
                self.city = False
                self.state_id = False
        else:
            super()._onchange_city_id()

    @api.constrains('email')
    def _check_if_email_is_valid(self):
        for record in self:
            if record.email:
                if not re.search("^[-!#$%&'*+/=?^_`{|}~.a-zA-Z0-9]+@[-a-zA-Z0-9]+(\.[-a-zA-Z0-9]+){1,}$", record.email):
                    raise ValidationError("Email yang dimasukkan '%s' tidak valid!"%(record.email))

    @api.onchange('email')
    def _lowercase_email(self):
        if self.email:
            self.email = self.email.lower()

    @api.constrains('phone', 'country_id')
    def _phone_validity_check(self):
        for record in self:
            if record.phone:
                # Use Odoo's built-in phone number validation utility
                try:
                    return phone_validation.phone_format(
                        record.phone,
                        record.country_id.code if record.country_id else None,
                        record.country_id.phone_code if record.country_id else None,
                        force_format='INTERNATIONAL',
                        raise_exception=True
                    )
                except (phonenumbers.phonenumberutil.NumberParseException, UserError) as e:
                    raise ValidationError(e) from e

    @api.constrains('mobile', 'country_id')
    def _mobile_validity_check(self):
        for record in self:
            if record.mobile:
                # Use Odoo's built-in phone number validation utility
                try:
                    return phone_validation.phone_format(
                        record.mobile,
                        record.country_id.code if record.country_id else None,
                        record.country_id.phone_code if record.country_id else None,
                        force_format='INTERNATIONAL',
                        raise_exception=True
                    )
                except (phonenumbers.phonenumberutil.NumberParseException, UserError) as e:
                    raise ValidationError(e) from e

    # Uppercasing some input fields since the user cannot be trusted to input data with proper
    # capitalization
    @api.onchange('name')
    def _onchange_uppercase_name(self):
        self.__class__._onchange_uppercase_field(self, 'name')

    @api.onchange('street')
    def _onchange_uppercase_street(self):
        self.__class__._onchange_uppercase_field(self, 'street')

    @api.onchange('street2')
    def _onchange_uppercase_street2(self):
        self.__class__._onchange_uppercase_field(self, 'street2')

    @api.onchange('city')
    def _onchange_uppercase_city(self):
        self.__class__._onchange_uppercase_field(self, 'city')

    @api.onchange('zip')
    def _onchange_uppercase_zip(self):
        self.__class__._onchange_uppercase_field(self, 'zip')

class MetalindoPartnerCategory(models.Model):
    _inherit = 'res.partner.category'

    lower_name = fields.Char(string='Lower Name')

    _sql_constraints = [
        ('lower_name_uniq', 'unique (lower_name)', 'Nama ini sudah ada. Mohon diisi yang lain!')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['lower_name'] = vals['name'].lower()
        return super(MetalindoPartnerCategory, self).create(vals_list)

    def write(self, vals):
        if vals.get('name'):
            vals['lower_name'] = vals['name'].lower()
        result = super(MetalindoPartnerCategory, self).write(vals)
        return result


# Dipindahkan ke vendor_code.py
# class MetalindoVendorCode(models.Model):
#     _name = "vendor.code"
#     _description = 'Vendor Code'
#     _inherit = ['mail.thread']
#     _check_company_auto = True

#     code = fields.Char(string="Vendor Prefix Code")
#     name = fields.Char(string="Location")
#     company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
#     partner_ids = fields.One2many('res.partner', 'code_id', 'Partners')
#     partner_count = fields.Integer(string='Vendor Count', compute='_compute_partner_count')

#     _sql_constraints = [
#         ('code_uniq', 'unique (code)', 'Vendor Prefix Code ini sudah digunakan. Mohon diisi yang lain!')
#         ]

#     def _compute_partner_count(self):
#         for record in self:
#             record.partner_count = self.env['res.partner'].search_count([('code_id', '=', record.id)])

#     def name_get(self):
#         result = []
#         for record in self:
#             if record.code:
#                 if record.code == _('New'):
#                     name = record.name
#                 else:
#                     name = '[%s] %s' % (record.code, record.name)
#             else:
#                 name = record.name
#             result.append((record.id, name))
#         return result

#     def action_show_vendor(self):
#         self.ensure_one()
#         # Jika ingin memberi judul/name action, mesti disebut full begini, tidak bisa hanya modifikasi action XML
#         kanban_id = self.env.ref('base.res_partner_kanban_view').id
#         tree_id = self.env.ref('base.view_partner_tree').id
#         form_id = self.env.ref('base.view_partner_form').id
#         action = {
#             'type': 'ir.actions.act_window', 
#             'name': self.name + ' / Vendors',
#             'res_model': 'res.partner',
#             'view_mode': 'kanban,tree,form', # Dengan 3 mode begini, maka harus diberi list views
#             'views': [(kanban_id, 'kanban'), (tree_id, 'tree'), (form_id, 'form')],
#             'search_view_id': self.env.ref('base.view_res_partner_filter').id,
#             'context': {
#                 'search_default_code_id': [self.id],
#                 'default_code_id': self.id,
#                 },
#             }
#         return action
