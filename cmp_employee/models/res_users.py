# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.tools.misc import format_date


class ResUsers(models.Model):
    _inherit = 'res.users'


    def internal_lookup_for_employee(self, item, **kwargs):

        if not item or not isinstance(item, dict):
            return self.browse()

        email = item.get('work_email')
        if email:
           return self.env['res.users'].search([('login', '=', email)], limit=1)

        return self.browse()

    # def internal_process_for_employee(self, item, sync_strategy=None, data_sync=None, **kwargs):
    #     """ Process data from external source to create or update res.partner as employee
    #     :param item: dict from external source
    #     :param sync_strategy: external.data.sync.strategy record
    #     :param data_sync: external.data.sync record
    #     :param kwargs: other parameter from external source
    #     :return: res.partner record
    #     """
    #
    #     partner = data_sync.get_internal_object()
    #     if not partner:
    #         partner = self.internal_lookup_for_employee(
    #             item, sync_strategy=sync_strategy, data_sync=data_sync, **kwargs)
    #
    #     input_dict = data_sync.prepare_input_external(item, **kwargs)
    #     internal_context = data_sync.get_internal_context()
    #     if not partner:
    #         partner = self.with_context(**internal_context).create([input_dict])[0]
    #     else:
    #         if not partner.employee_rank:
    #             input_dict['employee_rank'] = 1
    #         # ignore update bila sama
    #         for key in ['email','function','name']:
    #             if partner[key] == input_dict.get(key):
    #                 input_dict.pop(key, None)
    #
    #         if input_dict:
    #             partner.with_context(**internal_context).write(input_dict)
    #
    #     if not item.get('bank_name'):
    #         return
    #     bank = self.env['res.bank'].internal_process_for_employee(
    #         item, sync_strategy=sync_strategy, **kwargs
    #     )
    #     acc_number = item.get('no_rekening')
    #     nama_rekening = item.get('nama_rekening')
    #     if bank and nama_rekening and acc_number:
    #         acc = partner.bank_ids.filtered(lambda b: b.acc_number == acc_number and b.bank_id.id == bank.id)
    #         if acc:
    #             if not acc.allow_out_payment:
    #                 acc.with_context(mail_create_nosubscribe=True).write({
    #                     'acc_holder_name': nama_rekening,
    #                     'allow_out_payment': True
    #                 })
    #         else:
    #             partner.with_context(mail_create_nosubscribe=True).write({
    #                 'bank_ids': [(0, 0, {
    #                     'bank_id': bank.id,
    #                     'acc_number': acc_number,
    #                     'acc_holder_name': nama_rekening,
    #                     'allow_out_payment':True,
    #                 })]
    #             })
    #     return partner
