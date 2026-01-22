# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class MetalindoVendorCode(models.Model):
    _name = "vendor.code"
    _description = 'Vendor Code'

    code = fields.Char(string="Vendor Prefix Code")
    name = fields.Char(string="Location")
    company_id = fields.Many2one('res.company', string='Company')
    partner_ids = fields.One2many('res.partner', 'code_id', 'Partners')
    partner_count = fields.Integer(string='Vendor Count', compute='_compute_partner_count')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'Vendor Prefix Code ini sudah digunakan. Mohon diisi yang lain!')
        ]

    def _compute_partner_count(self):
        for record in self:
            record.partner_count = self.env['res.partner'].search_count([('code_id', '=', record.id)])

    def name_get(self):
        result = []
        for record in self:
            if record.code:
                if record.code == _('New'):
                    name = record.name
                else:
                    name = '[%s] %s' % (record.code, record.name)
            else:
                name = record.name
            result.append((record.id, name))
        return result

    def action_show_vendor(self):
        self.ensure_one()
        # Jika ingin memberi judul/name action, mesti disebut full begini, tidak bisa hanya modifikasi action XML
        kanban_id = self.env.ref('base.res_partner_kanban_view').id
        tree_id = self.env.ref('base.view_partner_tree').id
        form_id = self.env.ref('base.view_partner_form').id
        action = {
            'type': 'ir.actions.act_window', 
            'name': self.name + ' / Vendors',
            'res_model': 'res.partner',
            'view_mode': 'kanban,tree,form', # Dengan 3 mode begini, maka harus diberi list views
            'views': [(kanban_id, 'kanban'), (tree_id, 'tree'), (form_id, 'form')],
            'search_view_id': self.env.ref('base.view_res_partner_filter').id,
            'context': {
                'search_default_code_id': [self.id],
                'default_code_id': self.id,
                },
            }
        return action

