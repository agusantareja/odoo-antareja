# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.tools.misc import format_date


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_external_data_sync(self, external_id ,sync_strategy=None,**kwargs):

        external_app_name = kwargs.get('external_app_name') or (sync_strategy and sync_strategy.external_app_name)
        external_model = kwargs.get('external_model') or (sync_strategy and sync_strategy.external_model) or self._name
        domain = [('external_model', '=', external_model), ('external_app_name', '=', external_app_name),
                  ('internal_model', '=', self._name), ('external_odoo_id', '=', external_id)]
        ExternalDataSync = self.env['external.data.sync']
        if sync_strategy:
            data_sync = ExternalDataSync.search(domain + [('sync_strategy_id', '=', sync_strategy.id)],limit=1)
            data = data_sync and data_sync.get_internal_object()
            if data:
                return data_sync

        data_sync = ExternalDataSync.search(domain, limit=1)
        data = data_sync and data_sync.get_internal_object()
        if data:
            return data_sync
        return ExternalDataSync.browse()

    def internal_lookup_for_employee(self, item, **kwargs):
        if not item or not isinstance(item, dict):
            return self.browse()

        email = item.get('work_email')
        if not email:
            return self.browse()
        user = self.env['res.users'].search([('login', '=', email)], limit=1)

        if user and user.partner_id:
            return user.partner_id

        user = self.env['res.users'].search([('login', '=', email)], limit=1)

        if user and user.partner_id:
            return user.partner_id

        result = self.search([('is_company', '=', False), ('customer_rank', '=', 0), ('supplier_rank', '=', 0),
                              ('employee_rank', '>', 0), ('email', '=', email)], limit=1)

        if not result:
            result = self.search([('is_company', '=', False), ('customer_rank', '=', 0), ('supplier_rank', '=', 0),
                                  ('email', '=', email)], limit=1, order='id')

        return result

    def internal_process_for_employee_partner(self,data_external=None, data_update=None,sync_strategy=None, data_sync=None, **kwargs):
        """ Process data from external source to create or update res.partner as employee
        :param item: dict from external source
        :param data_update
        :param sync_strategy: external.data.sync.strategy record
        :param data_sync: external.data.sync record
        :param kwargs: other parameter from external source
        :return: res.partner record
        """
        partner = self or data_sync.get_internal_object() or self.internal_lookup_for_employee(
                    data_external, sync_strategy=sync_strategy, data_sync=data_sync, **kwargs
                )
        data_update = data_update or {}
        data_update['employee_rank'] = 1
        if partner:
            for key in ['email', 'function', 'name']:
                if partner[key] == data_update.get(key):
                    data_update.pop(key, None)
        # input_dict = data_sync.prepare_input_external(item, **kwargs)
        # internal_context = data_sync.get_internal_context()
        if not partner:
            partner = self.create([data_update])[0]
        else:
            if not partner.employee_rank:
                data_update['employee_rank'] = 1
            # ignore update bila sama
            for key in ['email','function','name']:
                if partner[key] == data_update.get(key):
                    data_update.pop(key, None)

            if data_update:
                partner.write(data_update)

        if not data_external.get('bank_name'):
            return partner
        bank = self.env['res.bank'].internal_process_for_employee(
            data_external, sync_strategy=sync_strategy, **kwargs
        )
        acc_number = data_external.get('no_rekening')
        nama_rekening = data_external.get('nama_rekening')
        if bank and nama_rekening and acc_number:
            acc = partner.bank_ids.filtered(lambda b: b.acc_number == acc_number and b.bank_id.id == bank.id)
            if acc:
                if not acc.allow_out_payment:
                    acc.with_context(mail_create_nosubscribe=True).write({
                        'acc_holder_name': nama_rekening,
                        'allow_out_payment': True
                    })
            else:
                partner.with_context(mail_create_nosubscribe=True).write({
                    'bank_ids': [(0, 0, {
                        'bank_id': bank.id,
                        'acc_number': acc_number,
                        'acc_holder_name': nama_rekening,
                        'allow_out_payment':True,
                    })]
                })
        return partner
