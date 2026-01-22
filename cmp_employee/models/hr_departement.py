# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.tools.misc import format_date



class Department(models.Model):
    _inherit = 'hr.department'

    def internal_lookup_for_department(self, item, sync_strategy=None,**kwargs):
        external_id = None
        if isinstance(item, list):
            external_id = item[0]
        if isinstance(item, dict):
            external_id = item.get('id')
        elif isinstance(item,  int):
            external_id = item
        if not  external_id:
            return self.browse()

        external_app_name = kwargs.get('external_app_name') or (sync_strategy and sync_strategy.external_app_name)
        external_model = kwargs.get('external_model')  or (sync_strategy and sync_strategy.external_model) or self._name
        domain = [('external_model','=',external_model),('external_app_name','=',external_app_name),('internal_model','=',self._name),('external_odoo_id', '=', external_id)]
        ExternalDataSync = self.env['external.data.sync']
        if sync_strategy:
            data = ExternalDataSync.search(domain+[('sync_strategy_id', '=', sync_strategy.id)], limit=1)
            if data:
                return data

        return ExternalDataSync.search(domain, limit=1)
