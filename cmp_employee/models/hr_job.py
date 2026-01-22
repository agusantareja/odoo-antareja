# -*- coding: utf-8 -*-
import json

from odoo import models, api, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class HRJob(models.Model):
    _inherit = 'hr.job'

    group_id = fields.Many2one('res.groups', string='Access Group')

    def internal_lookup_for_job(self, item, sync_strategy=None,**kwargs):
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
        data = ExternalDataSync.search(domain, limit=1)
        # Todo Bila dalam item terdapat 3 field bisa di lookup name, department_id, company_id

        return data

    def ensure_job_have_group(self):
        category = self.env.ref('cmp_employee.category_employee_job')
        for job in self:
            if not job.group_id:
                domain = [('name', '=', job.name), ('category_id', '=', category.id)]
                group = self.env['res.groups'].search(domain, limit=1)
                if not group:
                    _logger.info("Creating group for job %s", job.name)
                    group = self.env['res.groups'].create({
                        'name':job.name,
                        'category_id': category.id,
                    })
                job.group_id = group

    # def create_if_not_exist(self, item,sync_strategy=None,**kwargs):
    #     if not sync_strategy:
    #         sync_strategy = self.env.ref('cmp_employee.external_data_sync_strategy_hr_job')
    #     data_sync =  self.internal_lookup_for_job(item,   sync_strategy=sync_strategy, **kwargs)
    #
    #     def convert_to_dict(item_input):
    #         if isinstance(item_input, dict):
    #             return item_input
    #         if isinstance(item_input, list):
    #             return {
    #                 'id': item_input[0],
    #                 'display_name': item_input[1],
    #                 'name': item_input[1],
    #             }
    #         raise UserError("Invalid external id for job")
    #
    #     item = convert_to_dict(item)
    #     return
    # def internal_process_for_employee(self, item, sync_strategy=None, data_sync=None, **kwargs):
    #
    #     if not data_sync:
    #         data_sync = self.env['external.data.sync'].data_from_external(item, sync_strategy)
    #
    #     job = data_sync.get_internal_object()
    #     if not job:
    #         external_name = item.get('name') or item.get('display_name')
    #         job = self.create({'name':external_name})
    #         data_sync.write({
    #             'data_json': json.dumps(item),
    #             'internal_odoo_id':job.id,
    #         })
    #     return job
