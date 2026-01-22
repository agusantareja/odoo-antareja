# -*- coding: utf-8 -*-
import json

from odoo import models, api, fields, _, Command
from odoo.tools.misc import format_date

class HREmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee'

    def prepare_input_dict(self,item, input_dict={}):
        if not item or not isinstance(item, dict):
            return input_dict

        for field in ['name']:
            if field in item:
                input_dict[field] = item.get(field)
        return input_dict

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

    def internal_lookup_for_employee(self, item, sync_strategy=None,**kwargs):
        external_id = None
        if isinstance(item, list):
            external_id = item[0]
        if isinstance(item, dict):
            external_id = item.get('id')
        elif isinstance(item,  int):
            external_id = item
        if not  external_id:
            return self.browse()
        data_sync = self.get_external_data_sync(external_id ,sync_strategy=sync_strategy,**kwargs)
        data = data_sync.get_internal_object()
        if data:
            return data

        if isinstance(item, dict) :
            def get_by_field(field_name, value):
                return self.search([(field_name, '=', value)], limit=1)
            for f_name in ['nip','work_email']:
                result = f_name in item and get_by_field(f_name,item[f_name])
                if result:
                    return result

        return self.browse()

    def internal_process_for_employee(self, data_external=None, sync_strategy=None,
                                      data_update=None, data_sync=None, **kwargs):
        """ Process data from external source to create or update res.partner as employee
        :param data_external: dict from external source
        :param data_update: dict parse by system
        :param sync_strategy: external.data.sync.strategy record
        :param data_sync: external.data.sync record
        :param kwargs: other parameter from external source
        :return: res.partner record
        """
        if self:
            employee = self
        else:
            employee = self.internal_lookup_for_employee(
                data_external, sync_strategy=sync_strategy, data_sync=data_sync,input_dict=data_update, **kwargs
            )

        work_contact = None
        user = self.env['res.users'].internal_lookup_for_employee(data_external, **kwargs)
        if user:
            work_contact = user.partner_id
        # work_contact
        external_id = data_external.get('id')
        partner_sync_strategy = self.env.ref('cmp_employee.external_data_sync_strategy_intra_partner_employee')
        partner_data_sync = self.env['res.partner'].get_external_data_sync(external_id, partner_sync_strategy)
        if not work_contact:
            work_contact = self.env['res.partner'].internal_lookup_for_employee(
                data_external, sync_strategy=partner_sync_strategy, data_sync=partner_data_sync, **kwargs)
        elif partner_data_sync.internal_odoo_id and partner_data_sync.internal_odoo_id!=work_contact.id:
            partner_data_sync.write({
                'internal_odoo_id':work_contact.id
            })

        employee = data_sync.get_internal_object()
        if not employee:
            employee = self.internal_lookup_for_employee(
                data_external, sync_strategy=sync_strategy, data_sync=data_sync, **kwargs)

        if not employee and not isinstance(data_external, dict):
            data_external = data_sync.get_json_data_for_create()
            # coba lookup lagi
            employee = self.internal_lookup_for_employee(
                data_external, sync_strategy=sync_strategy, data_sync=data_sync, **kwargs
            )

        #input_dict = data_sync.prepare_input_external(item, **kwargs)
        if not employee or (user and employee.user_id.id != user.id ):
            data_update.update(user_id=user.id)
        if not employee or (work_contact and employee.work_contact_id.id != work_contact.id):
            data_update.update(work_contact_id=work_contact.id)
        return employee

    def internal_event_sync_done(self):
        employee = self
        # work_contact
        # external_id = item.get('id')
        # partner_sync_strategy = self.env.ref('cmp_employee.external_data_sync_strategy_intra_partner_employee')
        # partner_data_sync = self.env['res.partner'].get_external_data_sync(external_id, partner_sync_strategy)
        # if not work_contact:
        #     work_contact = self.env['res.partner'].internal_lookup_for_employee(
        #         item, sync_strategy=partner_sync_strategy, data_sync=partner_data_sync, **kwargs)
        # elif partner_data_sync.internal_odoo_id and partner_data_sync.internal_odoo_id!=work_contact.id:
        #     partner_data_sync.write({
        #         'internal_odoo_id':work_contact.id
        #     })
        #
        # employee = data_sync.get_internal_object()
        # if not employee:
        #     employee = self.internal_lookup_for_employee(
        #         item, sync_strategy=sync_strategy, data_sync=data_sync, **kwargs)
        #
        # if not employee and not isinstance(item, dict):
        #     item = data_sync.get_json_data_for_create()
        #     # coba lookup lagi
        #     employee = self.internal_lookup_for_employee(
        #         item, sync_strategy=sync_strategy, data_sync=data_sync, **kwargs)
        #
        # #input_dict = data_sync.prepare_input_external(item, **kwargs)
        # if not employee or (user and employee.user_id.id != user.id ):
        #     input_dict.update(user_id=user.id)
        # if not employee or (work_contact and employee.work_contact_id.id != work_contact.id):
        #     input_dict.update(work_contact_id=work_contact.id)

        # internal_context = data_sync.get_internal_context() or {}
        # def setup_internal_context():
        #     internal_context['skip_setup_employee_user_have_group']=True
        #     if employee.company_id:
        #         internal_context['default_company_id'] = employee.company_id.id
        #     if employee.department_id:
        #         internal_context['default_department_id'] = employee.department_id.id
        #
        # internal_context['tracking_disable'] = True
        # if employee:
        #     setup_internal_context()
        #     if input_dict:
        #         employee.with_context(**internal_context).write(input_dict)
        # else:
        #     employee = self.with_context(**internal_context).create([input_dict])[0]

        # if partner_data_sync.internal_odoo_id != work_contact.id:
        #     item_partner = dict(item)
        #     item_partner['job_position'] = employee.job_position
        #     partner_data_sync.write({
        #         'state':'draft',
        #         'data_json': json.dumps(item_partner),
        #         'internal_odoo_id': work_contact.id
        #     })
        return employee

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        employees = super().create(vals_list)
        for emp in employees:
            if emp.work_contact_id and emp.job_position and emp.job_position != emp.work_contact_id.function:
                emp.work_contact_id.function = emp.job_position
        return employees

    def write(self, vals):
        res = super().write(vals)
        if 'job_id' in vals:
            for emp in self:
                if emp.job_position and emp.job_position != emp.work_contact_id.function:
                    emp.work_contact_id.function = emp.job_position
        return res
