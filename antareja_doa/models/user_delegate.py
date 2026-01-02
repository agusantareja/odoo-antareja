# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools
from odoo.fields import Many2one, One2many, Many2many
from datetime import date
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)


class UserDelegate(models.Model):
    _name = 'user.delegate'
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
        [('send_to_delegatee_only', 'Send to Delegatee only'),
         ('send_to_both', 'Send to both Delegator and Delegatee')],
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

    @api.depends('delegator_id')
    def _compute_delegator_group_ids(self):
        for rec in self:
            if rec.delegator_id:
                rec.delegator_group_ids = rec.delegator_id.groups_id
            else:
                rec.delegator_group_ids = [(5, 0, 0)]

    proxy_id = fields.Many2one('res.users', string='Delegatee (Acting On Behalf)', tracking=True, related='delegatee_id', store=True, )
    delegatee_id = fields.Many2one(
        'res.users',
        string='Delegatee (Acting On Behalf)',
        tracking=True, store=True, readonly=False,
        help="User who will act on behalf of the delegator."
    )
    start_date = fields.Date(string='Start Date', required=True, tracking=True, )
    end_date = fields.Date(string='End Date', required=True, tracking=True, )
    note = fields.Text(string="Notes")

    def name_get(self):
        return [(record.id, f"[{record.name}] {record.delegator_id.name} to {record.delegatee_id.name}") for record in self]

    def ensure_set_number(self):
        name = self.name or 'Draft'
        if name in ['Draft', 'New'] and self.state != 'draft':
            find_dcr = True
            # Jika sudah ada, buat nomor baru sampai tidak ada yang sama
            while find_dcr:
                name = self.env['ir.sequence'].next_by_code('user.delegate') or 'Draft'
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

    def get_prepared_state(self):
        return ['prepared']

    is_prepared_condition = fields.Boolean(compute='compute_is_condition')
    is_edit_able_delegator_id = fields.Boolean(compute='compute_is_condition')
    is_able_button_revoke = fields.Boolean(compute='compute_is_condition')

    @api.depends('state')
    def compute_is_condition(self):
        for rec in self:
            rec.is_edit_able_delegator_id = rec.state == 'draft' and self.user_has_groups('base.group_erp_manager')
            rec.is_able_button_revoke = rec.state == 'active' and (
                    rec.delegator_id.id == self.env.user.id or self.user_has_groups('base.group_erp_manager'))
            rec.is_prepared_condition = rec.state in self.get_prepared_state() and (
                    rec.delegator_id.id == self.env.user.id or self.user_has_groups('base.group_erp_manager'))

    filter_user_delegate = fields.Boolean(store=False, search="search_filter_user_delegate")

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

    @api.model
    def get_proxy_for_user(self, user_id, company_id=None):
        today = date.today()
        domain = [
            ('delegator_id', '=', user_id),
            ('start_date', '<=', today),
            ('end_date', '>=', today),
            ('state', '=', 'active')
        ]
        if company_id:
            domain.extend([
                ('delegator_id.company_ids', '=', company_id),
                ('delegatee_id.company_ids', '=', company_id)
            ]
            )
        delegation = self.search(domain, )
        return delegation.delegatee_id if delegation else False

    def get_all_delegations_for_proxy(self, proxy_id=None, user_id=None, group_id=None, company_id=None, user_ids=None,
                                      limit=None):
        """
        Ambil delegasi aktif untuk proxy tertentu.
        Jika group_id diberikan, hanya delegator yang termasuk dalam grup tersebut.
        """
        today = date.today()
        domain = [
            ('start_date', '<=', today),
            ('end_date', '>=', today),
            ('state', '=', 'active'),
            ('active', '=', True),
        ]
        if company_id:
            domain.extend([
                ('delegator_id.company_ids', '=', company_id),
                ('delegatee_id.company_ids', '=', company_id)
            ])

        if proxy_id:
            if isinstance(proxy_id, list):
                domain.append(('delegatee_id', 'in', proxy_id))
            else:
                domain.append(('delegatee_id', '=', proxy_id))

        if user_id and group_id:
            raise ValidationError("You cannot filter by both user_id and group_id at the same time.")

        if user_ids:
            domain.append(('delegator_id', 'in', user_ids))
        elif user_id:
            if isinstance(user_id, list):
                domain.append(('delegator_id', 'in', user_id))
            else:
                domain.append(('delegator_id', '=', user_id))

        if group_id:
            # group = self.env['res.groups'].browse(group_id)
            domain.append(('delegator_id.groups_id', '=', group_id))

        return self.search(domain, limit=limit, order='start_date desc')

    def get_delegations_for_proxy(self, proxy_id, **kwargs):
        return self.get_all_delegations_for_proxy(proxy_id, limit=1, **kwargs)

    @tools.ormcache('delegatee_id')
    def get_delegations_user_group_for_proxy(self, proxy_id):
        # _logger.debug("Getting delegation info from DB for proxy_id=%s", proxy_id)
        # today = date.today()
        # domain = [
        #     ('start_date', '<=', today),
        #     ('end_date', '>=', today),
        #     ('state', '=', 'active'),
        #     ('proxy_id', '=', proxy_id)
        # ]
        # user_delegations = self.sudo.search(domain)
        # delegated_user_ids = list(set(user_delegations.mapped('delegator_id.id')))
        # delegated_group_ids = list(set(user_delegations.mapped('delegator_id.groups_id.id')))
        # return {
        #     'user_ids': delegated_user_ids,
        #     'group_ids': delegated_group_ids,
        # }
        #
        _logger.debug("Getting delegation info from DB for delegatee_id=%s (SQL)", proxy_id)
        self._cr.execute("""
                SELECT DISTINCT ud.id, ud.delegator_id, gu.gid
                FROM user_delegate ud
                JOIN res_groups_users_rel gu ON gu.uid = ud.delegator_id
                WHERE
                    ud.delegatee_id = %s
                    AND ud.state = 'active'
                    AND ud.start_date <= CURRENT_DATE
                    AND ud.end_date >= CURRENT_DATE
            """, (proxy_id,))
        rows = self._cr.fetchall()

        # Pisahkan jadi dua set
        user_ids = set()
        group_ids = set()
        user_delegate_ids = set()
        for udid, uid, gid in rows:
            user_ids.add(uid)
            group_ids.add(gid)
            user_delegate_ids.add(udid)

        return {
            'user_ids': list(user_ids),
            'group_ids': list(group_ids),
            'user_delegate_ids': list(user_delegate_ids),
        }

    @tools.ormcache('delegatee_id', 'group_id', 'company_id')
    def proxy_has_delegate_group_company(self, delegatee_id, group_id, company_id):
        """
        Checks this user as proxy user have DoA form delegator user given group delegator user to proxy user.
        """
        # today = date.today()
        # domain = [
        #     ('start_date', '<=', today),
        #     ('end_date', '>=', today),
        #     ('state', '=', 'active'),
        #     ('proxy_id', '=', proxy_id),
        #     ('proxy_id.company_ids', '=', company_id),
        #     ('delegator_id.company_ids', '=', company_id),
        #     ('delegator_id.groups_id', '=', group_id)
        # ]
        # base_groups_access = self.sudo().search(domain, limit=1)
        # return base_groups_access and True or False
        self._cr.execute("""
                SELECT 1
                FROM user_delegate ud
                JOIN res_groups_users_rel gu ON gu.uid = ud.delegator_id
                WHERE
                    ud.delegatee_id = %s
                    AND gu.gid = %s
                    AND ud.state = 'active'
                    AND ud.start_date <= CURRENT_DATE
                    AND ud.end_date >= CURRENT_DATE
                    AND ud.company_id = %s
                LIMIT 1
            """, (delegatee_id, group_id, company_id))
        return bool(self._cr.fetchone())

    @tools.ormcache('delegatee_id', 'group_id')
    def proxy_has_delegate_group(self, delegatee_id, group_id):
        """
        Checks this user as proxy user have DoA form delegator user given group delegator user to proxy user.
        """
        # today = date.today()
        # domain = [
        #     ('start_date', '<=', today),
        #     ('end_date', '>=', today),
        #     ('state', '=', 'active'),
        #     ('proxy_id', '=', proxy_id),
        #     ('delegator_id.groups_id', '=', group_id)
        # ]
        # base_groups_access = self.sudo().search(domain, limit=1)
        # return base_groups_access and True or False
        self._cr.execute("""
            SELECT 1
            FROM user_delegate ud
            JOIN res_groups_users_rel gu ON gu.uid = ud.delegator_id
            WHERE
                ud.delegatee_id = %s
                AND gu.gid = %s
                AND ud.state = 'active'
                AND ud.start_date <= CURRENT_DATE
                AND ud.end_date >= CURRENT_DATE
            LIMIT 1
        """, (delegatee_id, group_id))
        return bool(self._cr.fetchone())

    def _clear_delegatee_cache_if_needed(self, old_vals=None):
        """
        Bersihkan cache hanya jika:
        - state berubah menjadi atau dari 'active'
        - atau field penting pada delegasi aktif berubah
        """
        tracked_fields = {'start_date', 'end_date', 'delegator_id', 'delegatee_id', 'state'}

        for rec in self:
            need_clear = False

            # Jika tidak disediakan, bersihkan saja tanpa pengecekan
            if old_vals is None:
                need_clear = True
            else:
                # Cek perubahan state
                old_state = old_vals.get(rec.id, {}).get('state')
                new_state = rec.state
                if old_state != new_state and ('active' in (old_state, new_state)):
                    need_clear = True

                # Jika state tetap 'active', cek field lain berubah
                if old_state == 'active' and new_state == 'active':
                    for field in tracked_fields:
                        if field in old_vals.get(rec.id, {}):
                            need_clear = True
                            break

            if need_clear and rec.delegatee_id:
                _logger.debug("Clearing cache for delegatee_id=%s due to state/field change.", rec.delegatee_id.id)
                self.get_delegations_user_group_for_proxy.clear_cache(self, rec.delegatee_id.id)

                if rec.delegator_id:
                    for group in rec.delegator_id.groups_id:
                        self.proxy_has_delegate_group.clear_cache(self, rec.delegatee_id.id, group.id)

                        for company in rec.delegator_id.company_ids:
                            _logger.debug(
                                "Clearing cache for delegatee_id=%s, group_id=%s, company_id=%s",
                                rec.delegatee_id.id, group.id, company.id
                            )
                            self.proxy_has_delegate_group_company.clear_cache(
                                self, rec.delegatee_id.id, group.id, company.id
                            )

    def setup_number(self, vals):
        if vals.get('name', 'Draft') in ['Draft', 'New']:
            find_dcr = True
            while find_dcr:
                vals['name'] = self.env['ir.sequence'].next_by_code('user.delegate') or 'New'
                find_dcr = self.search([('name', '=', vals['name'])], limit=1)
        return vals

    # def write(self, vals):
    #     old_vals = {}
    #     if any(field in vals for field in ['state']):
    #         for rec in self:
    #             old_vals[rec.id] = {
    #                 field: rec[field] for field in vals.keys() if field in rec
    #             }
    #
    #     result = super().write(vals)
    #     if self.name in ['Draft', 'New']:
    #         if not self.env.context.get('__setup_number'):
    #             self = self.with_context(__setup_number=True)
    #             new_vals = self.setup_number({'name': self.name})
    #             self.write(new_vals)
    #             self.flush()
    #         else:
    #             return result
    #     # self._clear_proxy_cache_if_needed(old_vals)
    #     return result

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

    def unlink(self):
        active_records = self.filtered(lambda r: r.state == 'active')
        proxies = active_records.mapped('delegatee_id')
        res = super().unlink()
        for proxy in proxies:
            self.get_delegations_user_group_for_proxy.clear_cache(self, proxy.id)
        return res

    @api.constrains('delegator_id', 'delegatee_id', 'start_date', 'end_date', 'state')
    def _check_duplicate_active_delegation(self):
        for rec in self:
            if rec.state == 'cancelled':
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

    # def get_all_proxy_ids_for_delegator_ids(self, user_ids, company_id=None):
    #     """
    #     parameter list of user ids
    #     exclude proxy user yang sudah ada user_ids
    #     """
    #     if not user_ids:
    #         return None
    #     delegations = self.get_all_delegations_for_proxy(user_ids=user_ids, company_id=company_id)
    #     return list(
    #         set(d.proxy_id.id for d in delegations) - set(user_ids)
    #     )

    def get_all_delegations(self, delegatee_id=None, delegator_id=None, group_id=None, company_id=None, limit=None):
        """
        Ambil delegasi aktif untuk proxy tertentu.
        Jika group_id diberikan, hanya delegator yang termasuk dalam grup tersebut.
        """
        today = date.today()
        domain = [
            ('start_date', '<=', today),
            ('end_date', '>=', today),
            ('state', '=', 'active'),
            ('active', '=', True),
        ]
        if company_id:
            domain.extend([
                ('delegator_id.company_ids', '=', int(company_id)),
                ('delegatee_id.company_ids', '=', int(company_id))
            ])

        if delegatee_id:
            if isinstance(delegatee_id, list):
                domain.append(('delegatee_id', 'in', delegatee_id))
            else:
                domain.append(('delegatee_id', '=', delegatee_id))

        if delegator_id:
            if isinstance(delegator_id, list):
                domain.append(('delegator_id', 'in', delegator_id))
            else:
                domain.append(('delegator_id', '=', delegator_id))

        if group_id:
            if isinstance(group_id, list):
                domain.append(('group_id', 'in', group_id))
            else:
                domain.append(('group_id', '=', group_id))

        return self.search(domain, limit=limit, order='start_date desc,end_date')

    def get_notification_user_ids(self, delegator_ids, company_id=None):
        delegations = self.get_all_delegations(delegator_id=delegator_ids, company_id=company_id)
        result = []
        exclude_user_delegate = []
        for delegation in delegations:
            result.append(delegation.delegatee_id.id)
            if delegation.notification_option == 'send_to_delegatee_only':
                exclude_user_delegate.append(delegation.delegator_id.id)
            else:
                result.append(delegation.delegator_id.id)
        result.extend(set(delegator_ids) - set(exclude_user_delegate))
        return list(set(result))

    def get_all_delegatee(self, delegator_ids, company_id=None):
        """
        get delegatee_ids for this delegator_ids
        """
        if not delegator_ids:
            return []
        delegations = self.get_all_delegations(delegator_id=delegator_ids, company_id=company_id)
        return list(
            set(d.delegatee_id.id for d in delegations) - set(delegator_ids)
        )

    def get_all_delegator(self, delegatee_ids, company_id=None):
        """
        get delegator for this delegatee_ids
        """
        if not delegatee_ids:
            return []
        delegations = self.get_all_delegations(delegatee_id=delegatee_ids, company_id=company_id)
        return list(
            set(d.delegator_id.id for d in delegations) - set(delegatee_ids)
        )

    @api.model
    def read_user(self,user):
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
        if self.env.context.get('__from_sync_data_api'):
            if fields:
                if 'delegator_group_ids' in fields:
                    fields.remove('delegator_group_ids')

        result = super(UserDelegate,self).read(fields=fields,load=load)
        if self.env.context.get('__from_sync_data_api'):
            delegator = {}
            for rec in self:
                delegator[rec.id] = {
                    'write_date': rec.write_date,
                }
                if self.delegator_id and (not fields or (fields and 'delegator_id' in fields)) :
                    delegator[rec.id]['delegator_id']= self.read_user(rec.delegator_id)

                if self.delegatee_id and (not fields or (fields and 'delegatee_id' in fields)):
                    delegator[rec.id]['delegatee_id'] = self.read_user(rec.delegator_id)

            if len(result) > 0:
                for data in result:
                    if data['id'] not in delegator:
                        continue
                    data.update(
                        delegator[data['id']]
                    )

        return result