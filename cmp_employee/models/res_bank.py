# -*- coding: utf-8 -*-

import re

from collections.abc import Iterable

from odoo import api, fields, models, _
from odoo.osv import expression


class Bank(models.Model):
    _inherit = 'res.bank'

    def internal_process_for_employee(self, item, sync_strategy=None, data_sync=None, **kwargs):
        ExternalDataLookup = self.env['external.data.lookup']
        external_model = (data_sync.external_model if data_sync else None) or  \
                         (sync_strategy.external_model if sync_strategy else None) or \
                         'hr.employee'
        external_app_name = (data_sync.external_app_name if data_sync else None) or \
                            (sync_strategy.external_app_name if sync_strategy else None)

        bank_name = item.get('bank_name')
        if not bank_name:
            return self.browse()

        bank_lookup = ExternalDataLookup.search(
            [('name', '=', bank_name),
             ('external_model', '=', external_model),
             ('external_app_name', '=', external_app_name),
             ('internal_model', '=', 'res.bank'),
             ('internal_id', '>', 0)]
        )

        if not bank_lookup:
            bank = self.env['res.bank'].search([('name', '=', bank_name)], limit=1)
            if not bank:
                bank = self.env['res.bank'].create({'name': bank_name})
            ExternalDataLookup.create({
                'name': bank_name,
                'external_model': external_model,
                'external_app_name': external_app_name,
                'internal_model': 'res.bank',
                'internal_id': bank.id
            })
        else:
            bank = self.env['res.bank'].browse(bank_lookup.internal_id)

        return bank
