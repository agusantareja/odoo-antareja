# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from odoo.fields import Many2one, One2many, Many2many
from datetime import date
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class UserDelegation(models.Model):
    _name = 'user.delegation'
    _description = 'User Delegation'
    _order = 'start_date desc'
    _inherit = ['mail.thread']

    active = fields.Boolean(default=True)
    name = fields.Char(
        string='Delegation Number',
        default='Draft',
        required=True,
        tracking=True,
        copy=False
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        string='Company', tracking=True,
        help="Company for which the delegation is valid."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('prepared', 'Prepared'),
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ], string='State', default='draft', tracking=True)

    notification_option = fields.Selection(
        [('send_to_delegatee_only', 'Notif to Delegatee Only'),
         ('send_to_both', 'Notif to delegator & delegatee')],
        default='send_to_both'
    )

    delegator_id = fields.Many2one(
        'res.users', string='Delegator', required=True, tracking=True, default=lambda self: self.env.user)
    delegator_group_ids = fields.Many2many(
        'res.groups',
        string='Delegator Groups',
        compute='_compute_delegator_group_ids',
        store=False,  # jika ingin nilainya disimpan di DB
        readonly=True,  # agar tidak bisa diubah manual
        help="Groups of the delegator user. Used for filtering delegations."
    )

    delegatee_id = fields.Many2one(
        'res.users',
        string='Delegatee (Acting On Behalf)',
        tracking=True, store=True, readonly=False,
        help="User who will act on behalf of the delegator."
    )
    start_date = fields.Date(string='Start Date', required=True, tracking=True, )
    end_date = fields.Date(string='End Date', required=True, tracking=True, )
    note = fields.Text(string="Notes")
    is_prepared_condition = fields.Boolean(compute='compute_is_condition')
    is_edit_able_delegator_id = fields.Boolean(compute='compute_is_condition')
    is_able_button_revoke = fields.Boolean(compute='compute_is_condition')
    filter_user_delegate = fields.Boolean(store=False, search="search_filter_user_delegate")

    @api.depends('delegator_id')
    def _compute_delegator_group_ids(self):
        doa_group = self.env['res.users'].doa_exclude_groups()
        for rec in self:
            if rec.delegator_id:
                rec.delegator_group_ids = rec.delegator_id.groups_id - rec.delegatee_id.groups_id - doa_group
            else:
                rec.delegator_group_ids = [(5, 0, 0)]

    def name_get(self):
        return [(record.id, f"[{record.name}] {record.delegator_id.name} to {record.delegatee_id.name}") for record in
                self]

    def ensure_set_number(self):
        name = self.name or 'Draft'
        if name in ['Draft', 'New'] and self.state != 'draft':
            find_dcr = True
            # Jika sudah ada, buat nomor baru sampai tidak ada yang sama
            while find_dcr:
                name = self.env['ir.sequence'].next_by_code('user.delegation') or 'Draft'
            self.write({'name': name})

    def _set_prepared_state(self):
        self.ensure_one()
        self.ensure_set_number()
        if self.state in ['cancelled', 'expired']:
            return
        else:
            self.ensure_state()

    def ensure_state(self):
        today = date.today()
        if self.start_date <= today <= self.end_date:
            self.state = 'active'
        elif self.start_date > today:
            self.state = 'prepared'
        elif self.end_date < today:
            self.state = 'expired'

    def action_button_submit(self):
        self._set_prepared_state()

    def action_button_cancel(self):
        self.state = 'cancelled'

    def action_button_revoke(self):
        self.state = 'expired'

    @api.model
    def get_prepared_state(self):
        return ['prepared']

    @api.depends('state')
    def compute_is_condition(self):
        for rec in self:
            rec.is_edit_able_delegator_id = rec.state == 'draft' and self.user_has_groups('base.group_erp_manager')
            rec.is_able_button_revoke = rec.state == 'active' and (
                    rec.delegator_id.id == self.env.user.id or self.user_has_groups('base.group_erp_manager'))
            rec.is_prepared_condition = rec.state in self.get_prepared_state() and (
                    rec.delegator_id.id == self.env.user.id or self.user_has_groups('base.group_erp_manager'))

    def search_filter_user_delegate(self, operator, operand):
        if self.user_has_groups('base.group_erp_manager'):
            return []
        else:
            return ['|', ('delegator_id', '=', self.env.user.id), ('delegatee_id', '=', self.env.user.id)]

    def cron_update_delegation_state(self):
        """
        Cron job to update the state of delegations based on current date.
        """
        delegations = self.search([('state', 'in', self.get_prepared_state())])
        for delegation in delegations:
            delegation.ensure_state()
            delegation.ensure_set_number()

    @api.constrains('delegator_id', 'delegatee_id')
    def _check_different_users(self):
        for rec in self:
            if rec.delegator_id == rec.delegatee_id:
                raise ValidationError("Delegator and Delegatee cannot be the same user.")

    def setup_number(self, vals):
        if vals.get('name', 'Draft') in ['Draft', 'New']:
            find_dcr = True
            while find_dcr:
                vals['name'] = self.env['ir.sequence'].next_by_code('user.delegation') or 'New'
                find_dcr = self.search([('name', '=', vals['name'])], limit=1)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        new_vals_list = []
        for vals in vals_list:
            new_vals_list.append(self.setup_number(vals))

        records = super().create(new_vals_list)

        # Hapus cache hanya untuk yang state-nya langsung 'active'
        # active_records = records.filtered(lambda r: r.state == 'active')
        # active_records._clear_proxy_cache_if_needed()
        return records

    @api.constrains('delegator_id', 'delegatee_id', 'start_date', 'end_date', 'state')
    def _check_duplicate_active_delegation(self):
        for rec in self:
            if self.state in ['cancelled', 'expired']:
                continue
            overlaps = self.search([
                ('id', '!=', rec.id),
                ('state', '=', 'active'),
                ('delegator_id', '=', rec.delegator_id.id),
                ('delegatee_id', '=', rec.delegatee_id.id),
                ('start_date', '<=', rec.end_date),
                ('end_date', '>=', rec.start_date),
            ])
            if overlaps:
                raise ValidationError("Duplicate active delegation with overlapping period found.")

    @api.model
    def read_user(self, user):
        # expectasi bahwa res.users hanya akan lookup saja tanpa melakukanan create bila tidak ditemukan
        # pencarian bisa menggunakan email atau id di aplikasi penerima

        if not user:
            return None
        return {
            'id': user.id,
            'name': user.name,
            'login': user.login,
            'email': user.email,
        }

    def read(self, fields=None, load='_classic_read'):
        if self.env.context.get('__from_sync_data_api') or self.env.context.get('__read_data_for_sync_external_application'):
            if fields:
                if 'delegator_group_ids' in fields:
                    fields.remove('delegator_group_ids')

        result = super(UserDelegation, self).read(fields=fields, load=load)
        if self.env.context.get('__from_sync_data_api') or self.env.context.get('__read_data_for_sync_external_application'):
            delegator = {}
            for rec in self:
                delegator[rec.id] = {
                    'write_date': rec.write_date,
                }
                if rec.delegator_id and (not fields or (fields and 'delegator_id' in fields)):
                    delegator[rec.id]['delegator_id'] = self.read_user(rec.delegator_id)

                if rec.delegatee_id and (not fields or (fields and 'delegatee_id' in fields)):
                    delegator[rec.id]['delegatee_id'] = self.read_user(rec.delegatee_id)

            if len(result) > 0:
                for data in result:
                    if data['id'] not in delegator:
                        continue
                    data.update(
                        delegator[data['id']]
                    )

        return result
