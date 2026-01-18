import base64
from odoo import _, api, fields, models
import requests
import json
import logging
from datetime import datetime, timedelta, date
from odoo.exceptions import Warning, UserError
from odoo.addons.amr_data_sync.tools.utils import insert_sql

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def prepare_input_dict(self, item, input_dict=None, sync_strategy=None, **kwargs):
        """ Process data from external source to create or update res.partner as employee
                :param item: dict from external source
                :param sync_strategy: external.data.sync.strategy record
                :param data_sync: external.data.sync record
                :param kwargs: other parameter from external source
                :return: res.partner record
                """
        input_dict = input_dict or {}
        # # ,a.email as work_email
        # if not input_dict.get('work_email'):
        #     input_dict['work_email'] = item.get('email')
        # # ,a.no_telp as mobile_phone
        # if not input_dict.get('mobile_phone'):
        #     input_dict['mobile_phone'] = item.get('no_telp')
        # # ,a.resign_date as termination_date
        # if not input_dict.get('termination_date'):
        #     input_dict['termination_date'] = item.get('resign_date')
        #
        # # ,case when a.jenis_kelamin = 'laki-laki' then 'male'
        # #         when a.jenis_kelamin = 'perempuan' then 'female'
        # #         end as gender
        # if not input_dict.get('gender'):
        #     jenis_kelamin = item.get('jenis_kelamin')
        #     if jenis_kelamin == 'laki-laki':
        #         input_dict['gender'] = 'male'
        #     elif jenis_kelamin == 'perempuan':
        #         input_dict['gender'] = 'female'

        # ,concat('%s/web/image?model=hr.employee&field=image_128&id=',a.id) as image_url

        input_dict

    def external_data_sync_done(self, **kwargs):
        # dipanggil saat done
        # self.create_user()
        # self.create_tapping()
        return
