# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrJob(models.Model):
    _inherit = "hr.department"

    def prepare_input_dict(self, item, input_dict=None, sync_strategy=None, **kwargs):
        """ Process data from external source to create or update res.partner as employee
                :param item: dict from external source
                :param sync_strategy: external.data.sync.strategy record
                :param data_sync: external.data.sync record
                :param kwargs: other parameter from external source
                :return: res.partner record
                """
        input_dict = input_dict or {}
        return input_dict

    def external_data_sync_done(self, **kwargs):
        # dipanggil saat done
        # self.create_user()
        # self.create_tapping()
        return

    # def internal_lookup_for_department(self, item, sync_strategy=None, **kwargs):
    #     external_id = None
    #     if isinstance(item, list):
    #         external_id = item[0]
    #     if isinstance(item, dict):
    #         external_id = item.get('id')
    #     elif isinstance(item, int):
    #         external_id = item
    #     if not external_id:
    #         return self.browse()
    #
    #     external_app_name = kwargs.get('external_app_name') or (sync_strategy and sync_strategy.external_app_name)
    #     external_model = kwargs.get('external_model') or (sync_strategy and sync_strategy.external_model) or self._name
    #     domain = [('external_model', '=', external_model), ('external_app_name', '=', external_app_name),
    #               ('internal_model', '=', self._name), ('external_odoo_id', '=', external_id)]
    #     ExternalDataSync = self.env['external.data.sync']
    #
    #     if sync_strategy:
    #         data = ExternalDataSync.search(domain + [('sync_strategy_id', '=', sync_strategy.id)], limit=1)
    #     if not data:
    #         data = ExternalDataSync.search(domain, limit=1)
    #
    #     obj = (data and data.get_internal_object())
    #     if obj:
    #         return obj
    #
    #     if external_id and (
    #             self.env.context.get('__hr_department_id_offset') or self.env.context.get(
    #         '__hr_department_id_same_as_external')):
    #         internal_id = external_id + self.env.context.get('__hr_department_id_offset', 0)
    #         return self.search([('id', '=', internal_id)])
    #
    #     return self.browse()
    #
    # def internal_process_for_department(self, item, sync_strategy=None, data_sync=None, **kwargs):
    #     """ Process data from external source to create or update res.partner as employee
    #     :param item: dict from external source
    #     :param sync_strategy: external.data.sync.strategy record
    #     :param data_sync: external.data.sync record
    #     :param kwargs: other parameter from external source
    #     :return: res.partner record
    #     """
    #     # chek apakah punya user
    #     if not data_sync:
    #         raise UserError("No data sync")
    #
    #     department = data_sync.get_internal_object()
    #     if not department:
    #         department = self.internal_lookup_for_department(item, sync_strategy=sync_strategy, data_sync=data_sync,
    #                                                          **kwargs)
    #
    #     if not department and not isinstance(item, dict):
    #         item = data_sync.get_json_data_for_create()
    #         # coba lookup lagi
    #         department = self.internal_lookup_for_department(item, sync_strategy=sync_strategy, data_sync=data_sync,
    #                                                          **kwargs)
    #     input_dict = data_sync.prepare_input_external(item, sync_strategy=sync_strategy, **kwargs)
    #     if department and input_dict:
    #         internal_context = data_sync.get_internal_context() or {}
    #         if department.company_id:
    #             internal_context['default_company_id'] = department.company_id.id
    #         internal_context['tracking_disable'] = True
    #         department.with_context(**internal_context).write(input_dict)
    #     else:
    #         self.env.cr.commit()
    #         if self.env.context.get('__hr_department_id_offset') or self.env.context.get(
    #                 '__hr_department_id_same_as_external'):
    #             external_id = item.get('id')
    #             internal_id = external_id + self.env.context.get('__hr_department_id_offset', 0)
    #             input_dict['id'] = internal_id
    #             department = insert_sql(self, [{'stored': input_dict}])[0]
    #         else:
    #             department = self.create([input_dict])[0]
    #
    #     return department
