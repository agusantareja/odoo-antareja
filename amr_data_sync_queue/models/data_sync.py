# -*- coding: utf-8 -*-

import datetime
import json
import logging
import traceback
from collections import defaultdict

from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.addons.amr_jsonrpc.utils import savepoint
from odoo.exceptions import UserError
from odoo.tools import date_utils

from ..tools.utils import convert_from_external_data, insert_data_sql

_logger = logging.getLogger(__name__)


class ExternalDataSync(models.Model):
    _inherit = 'external.data.sync'

    on_queue = fields.Boolean(default=False,)

    def process_data(self):
        try:
           super().process_data()
        finally:
            self.write({'on_queue': False})

    def write_error_safe(self,error_data,using_pool=False):
        error_data['on_queue']=False
        super().write_error_safe(error_data,using_pool=using_pool)

    def dispatch_process(self,run_immediate=False):
        self.write({'on_queue': True,'state':'process'})
        self.with_delay().process_data()

    def cron_process_data(self, limit=1000):
        # def process_rec_id(id_):
        #     with self.pool.cursor() as cr:
        #         env = api.Environment(cr, self.env.uid, self.env.context)
        #         rec = env[self._name].browse(id_)
        #         try:
        #             rec.process_data()
        #             cr.commit()
        #         except Exception :
        #             _logger.exception("Error rec %s", rec_id)
        #             cr.rollback()
        #             rec = env[self._name].browse(id_)
        #             rec.write_error_safe({
        #                 'error_info': traceback.format_exc(),
        #                 'state': 'error',
        #                 'last_error': fields.Datetime.now(),
        #                 'next_processing_datetime': fields.Datetime.now() + datetime.timedelta(hours=1),
        #             })
        # def process_related_id(id_):
        #     with self.pool.cursor() as cr:
        #         env = api.Environment(cr, self.env.uid, self.env.context)
        #         rec = env['external.data.sync.related'].browse(id_)
        #         try:
        #             rec.process_data()
        #             if rec.state != 'done' or not rec.external_data_sync_id:
        #                 rec.write({
        #                     'next_processing_datetime': fields.Datetime.now() + datetime.timedelta(hours=1),
        #                 })
        #             cr.commit()
        #         except Exception :
        #             _logger.exception("Error rec %s", rec_id)
        #             cr.rollback()
        #             rec = env[self._name].browse(id_)
        #             rec.write_error_safe({
        #                 'error_info': traceback.format_exc(),
        #                 'state': 'error',
        #                 'last_error': fields.Datetime.now(),
        #                 'next_processing_datetime': fields.Datetime.now() + datetime.timedelta(hours=1),
        #             })
        #limit_time = fields.Datetime.now() + datetime.timedelta(minutes=10)
        records  = self.search(
            [('on_queue','=',False),('need_get_data_json', '=', True)],
            limit=limit, order='next_processing_datetime asc,last_processing_datetime asc, id '
        )
        for rec in records :
            rec.dispatch_process()

        records =self.search(
            [('on_queue','=',False),('state', '!=', 'done'),
             '|',
             ('next_processing_datetime', '<=', fields.Datetime.now()),
             ('next_processing_datetime', '=', False)],
            limit=limit, order='next_processing_datetime asc,last_processing_datetime asc, id '
        )
        for rec in records :
            rec.dispatch_process()

        # sync_related = self.env['external.data.sync.related'].search(
        #     [('on_queue','=',False),('state', '!=', 'done'),
        #      '|',
        #      ('next_processing_datetime', '<=', fields.Datetime.now()),
        #      ('next_processing_datetime', '=', False)],
        #     order='next_processing_datetime', limit=limit, )
        # external_data_sync = self.browse()
        # limit_time = fields.Datetime.now() + datetime.timedelta(minutes=10)
        #
        # for t in sync_related:
        #     process_related_id(t.id)
        #     if t.state == 'done' and t.external_data_sync_id:
        #         external_data_sync |= t.external_data_sync_id
        #     if fields.Datetime.now() > limit_time:
        #         break
        # limit_time = fields.Datetime.now() + datetime.timedelta(minutes=10)
        # for t in external_data_sync:
        #     process_rec_id(t.id)
        #
        #     if fields.Datetime.now() > limit_time:
        #         break
        #
        # return True

    # def get_internal_context(self):
    #     return self.sync_strategy_id.get_internal_context()
    #
    # def get_internal_object(self, model=None):
    #     if not isinstance(model, models.BaseModel) and self.sync_strategy_id:
    #         model = self.sync_strategy_id.internal_model_object()
    #     if not isinstance(model, models.BaseModel)  and self.internal_model:
    #         model = self.env[self.internal_model]
    #     if isinstance(model, models.BaseModel):
    #         return model.with_context(active_test=False).browse(self.internal_odoo_id)
    #     return model
    #
    # # @savepoint
    # def process_field_after_create(self, existing):
    #     after_create = {}
    #     need_resolve = False
    #     for r in self.related_ids:
    #         if r.field_after_create or r.state != 'done':
    #             r.process_field_after_create()
    #         if r.field_type == 'many2one':
    #             data_relation = r.get_data_relation()
    #             if data_relation:
    #                 after_create[r.name] = data_relation
    #         if r.state != 'done':
    #             need_resolve = True
    #
    #     if after_create and existing:
    #         existing.write(after_create)
    #
    #     if need_resolve:
    #         self.write_error_safe({
    #             'error_info': "Issue Process Field After Create",
    #             'state': 'need_resolve',
    #             # 'last_error': fields.Datetime.now(),
    #             'next_processing_datetime': fields.Datetime.now() + datetime.timedelta(hours=1),
    #         })
    #     return after_create
    #
    # def action_process_field_after_create(self):
    #     for rec in self.filtered(lambda r: r.state == 'done' and r.internal_odoo_id):
    #         existing = rec.get_internal_object()
    #         if existing:
    #             rec.process_field_after_create(existing)
    #
    # def get_last_sync_datetime(self, strategy):
    #     domain = [
    #         ('sync_strategy_id', '=', strategy.id),
    #         ('state', '=', 'done'),
    #         ('internal_odoo_id', '!=', False),
    #     ]
    #     last_sync = self.search(domain, order='last_success desc', limit=1)
    #     if last_sync:
    #         return last_sync.last_success
    #     return None
    #
    # # def get_sync_strategy(self):
    # #     return self.sync_strategy_id.ensure_internal_context()
    #
    # def get_or_create(self, external_data, sync_strategy):
    #     external_data = self.ensure_external_data(external_data)
    #     external_odoo_id = external_data.get('id')
    #     domain = [
    #         ('external_odoo_id', '=', external_odoo_id),
    #         ('sync_strategy_id', '=', sync_strategy.id)
    #     ]
    #     existing = self.search(domain, limit=1)
    #     if existing:
    #         return existing
    #     else:
    #         return self.data_from_external(external_data, sync_strategy)
    #
    # def reverse_mapping(
    #         self, internal,
    #         sync_strategy=None,
    #         external_app_name=None,
    #         external_model=None,
    #         raise_not_found_exception=True
    # ):
    #     # return result_map(int:internal_id,list():external_id), not_mapped_ids(int:internal)
    #     # digunakan untuk mengirim data ke server external
    #     if not internal:
    #         return [], []
    #
    #     if not isinstance(internal, models.BaseModel):
    #         _logger.error("Internal Object must")
    #         if raise_not_found_exception:
    #             raise ValueError("Internal Object must")
    #         return [], []
    #
    #     if sync_strategy:
    #         result_map, not_mapped_ids = sync_strategy.reverse_mapping(internal, raise_not_found_exception=False)
    #         if not not_mapped_ids:
    #             return result_map, not_mapped_ids
    #         internal_model = sync_strategy.internal_model
    #         external_app_name = sync_strategy.get_external_application_name()
    #         external_model = sync_strategy.external_model or internal_model
    #     else:
    #         internal_model = internal._name
    #         result_map, not_mapped_ids = {}, set(internal.ids)
    #
    #     if not external_app_name:
    #         _logger.error("external_app_name not set")
    #         if raise_not_found_exception:
    #             raise ValueError("external_app_name not set")
    #         return result_map, not_mapped_ids
    #     if not external_model:
    #         if internal_model:
    #             external_model = internal_model
    #         else:
    #             _logger.error("external_model not set")
    #             if raise_not_found_exception:
    #                 raise ValueError("external_model not set")
    #             return result_map, not_mapped_ids
    #
    #     domain = [('internal_odoo_id', 'in', list(not_mapped_ids)), ('internal_model', '=', internal_model),
    #               ('external_app_name', '=', external_app_name), ('external_model', '=', external_model), ]
    #
    #     rows = self.search_read(
    #         domain,
    #         fields=['internal_odoo_id', 'external_odoo_id']
    #     )
    #
    #     mapping = defaultdict(list)
    #     for r in rows:
    #         mapping[r['internal_odoo_id']].append(r['external_odoo_id'])
    #
    #     result_map.update(dict(mapping))
    #     not_mapped_ids -= result_map.keys()
    #
    #     if not not_mapped_ids:
    #         return result_map, not_mapped_ids
    #
    #     domain = [('internal_id', 'in', list(not_mapped_ids)), ('internal_model', '=', internal_model),
    #               ('external_app_name', '=', external_app_name), ('external_model', '=', external_model),
    #               ('reverse_able', '=', True), ]
    #
    #     rows = self.env['external.data.lookup'].search_read(
    #         domain,
    #         fields=['internal_id', 'external_id']
    #     )
    #     mapping = defaultdict(list)
    #     for r in rows:
    #         mapping[r['internal_id']].append(r['external_id'])
    #
    #     result_map.update(dict(mapping))
    #
    #     if not_mapped_ids:
    #         _logger.error("found not mapped data")
    #         if raise_not_found_exception:
    #             raise ValueError("found not mapped data [%s]" % str(not_mapped_ids))
    #
    #     return result_map, not_mapped_ids
    #
    # @api.model
    # def ensure_external_data(self, external_data):
    #     if isinstance(external_data, dict):
    #         return external_data
    #     if isinstance(external_data, list):
    #         if len(external_data) == 2:
    #             return {
    #                 'id': external_data[0],
    #                 'display_name': external_data[1]
    #             }
    #         elif external_data:
    #             return {
    #                 'id': external_data[0],
    #             }
    #
    #     if isinstance(external_data, int):
    #         return {
    #             'id': external_data
    #         }
    #     return {}
    #
    # def action_build_payload(self):
    #     item = self.get_json_data_for_create()
    #     input_dict = self.prepare_input_external(item)
    #     self.payload_json = json.dumps(input_dict, default=date_utils.json_default)
    #
    # def data_from_external_id(self, external_odoo_id, sync_strategy):
    #     if not sync_strategy:
    #         raise UserError("Sync Strategy Not found")
    #     domain = [
    #         ('external_odoo_id', '=', external_odoo_id),
    #         ('sync_strategy_id', '=', sync_strategy.id)
    #     ]
    #     existing = self.search(domain, limit=1)
    #     if existing:
    #         return existing
    #     else:
    #         item = sync_strategy.get_external_one_data(external_odoo_id)
    #         external_last_update = item.get('write_date')
    #         display_name = item.get('display_name') or item.get('name')
    #
    #         if isinstance(external_last_update, str):
    #             external_last_update = fields.Datetime.to_datetime(external_last_update)
    #         input_dict = {
    #             'display_name': display_name or f'ID {external_odoo_id}',
    #             'external_last_update': external_last_update,
    #             'sync_strategy_id': sync_strategy.id,
    #             'data_json': json.dumps(item),
    #         }
    #         internal = sync_strategy.internal_lookup(item)
    #         if internal:
    #             input_dict.update(
    #                 internal_odoo_id=internal.id,
    #                 state='done',
    #                 last_success=fields.Datetime.now(),
    #             )
    #         existing = self.create([input_dict])[0]
    #
    #     return existing
