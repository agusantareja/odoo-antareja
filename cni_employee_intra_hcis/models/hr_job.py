
from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
import logging
import requests
import json
from odoo.exceptions import UserError, ValidationError



class HrJob(models.Model):
    _inherit = "hr.job"

    def internal_lookup_for_job(self, item, sync_strategy=None,**kwargs):
        external_id = None
        if isinstance(item, list):
            external_id = item[0]
        if isinstance(item, dict):
            external_id = item.get('id')
        elif isinstance(item,  int):
            external_id = item
        if not external_id:
            return self.browse()

        external_app_name = kwargs.get('external_app_name') or (sync_strategy and sync_strategy.external_app_name)
        external_model = kwargs.get('external_model')  or (sync_strategy and sync_strategy.external_model) or self._name
        domain = [('external_model','=',external_model),('external_app_name','=',external_app_name),('internal_model','=',self._name),('external_odoo_id', '=', external_id)]
        ExternalDataSync = self.env['external.data.sync']

        if sync_strategy:
            data = ExternalDataSync.search(domain+[('sync_strategy_id', '=', sync_strategy.id)], limit=1)
        if not data:
            data = ExternalDataSync.search(domain, limit=1)

        obj =  (data and data.get_internal_object())
        if obj:
            return obj

        if external_id and (self.env.context.get('__hr_job_id_offset') or self.env.context.get('__hr_job_id_same_as_external')):
            internal_id = external_id + self.env.context.get('__hr_job_id_offset',0)
            return self.browse(internal_id)

        return self.browse()


    def internal_process_for_job(self, item, sync_strategy=None, data_sync=None, **kwargs):
        """ Process data from external source to create or update res.partner as employee
        :param item: dict from external source
        :param sync_strategy: external.data.sync.strategy record
        :param data_sync: external.data.sync record
        :param kwargs: other parameter from external source
        :return: res.partner record
        """
        # chek apakah punya user
        if not data_sync:
            raise UserError("No data sync")

        job = data_sync.get_internal_object()
        if not job:
            job = self.internal_lookup_for_job(item, sync_strategy=sync_strategy, data_sync=data_sync, **kwargs)

        if not job and not isinstance(item, dict):
            item = data_sync.get_json_data_for_create()
            # coba lookup lagi
            job = self.internal_lookup_for_employee(item, sync_strategy=sync_strategy, data_sync=data_sync, **kwargs)

        if not job and (self.env.context.get('__hr_job_id_offset') or self.env.context.get('__hr_job_id_same_as_external')):
            external_id = item.get('id')
            name = item.get('name')
            internal_id = external_id + self.env.context.get('__hr_job_id_offset', 0)
            self.env.cr.execute("""
                    INSERT INTO hr_job (id, name, create_uid, create_date, write_uid, write_date)
                    VALUES (%s,%s, %s, %s, NOW(), %s, NOW())
                """, (internal_id,
                name,
                self.env.uid,
                self.env.uid
            ))
            data_sync.write({'internal_id':internal_id})
            self.env.cr.commit()
            job=self.browse(internal_id)

        input_dict = data_sync.prepare_input_external(item, **kwargs)
        internal_context = data_sync.get_internal_context() or {}

        if job.company_id:
            internal_context['default_company_id'] = job.company_id.id
        internal_context['tracking_disable'] = True

        if job:
            if input_dict:
                job.with_context(**internal_context).write(input_dict)
        else:
            job = self.with_context(**internal_context).create([input_dict])[0]
        return job

    # job_class_external_id = fields.Many2one('job.class.external', string='Job Class External')
    # parent_id = fields.Many2one('hr.job', string='Superior')
    # active = fields.Boolean(string='Active', default = True)


    