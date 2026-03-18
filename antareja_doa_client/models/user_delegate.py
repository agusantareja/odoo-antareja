# -*- coding: utf-8 -*-
import requests
from odoo import models, fields, api
from odoo.addons.base.models.ir_fields import exclude_ref_fields
from odoo.exceptions import UserError
from odoo.tools import image_process
import json
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class UserDelegate(models.Model):
    _name = 'user.delegate'
    _inherit = [
        _name, 'doa.server.mixin'
    ]

    def prepare_input_dict(self, item, input_dict=None, **kwargs):
        delegator = self.lookup_user_external_data(item.get('delegator_id'))
        delegatee = self.lookup_user_external_data(item.get('delegatee_id'))

        if delegator:
            input_dict['delegator_id'] = delegator.id
        else:
            raise ValidationError("Delegator user not found in external data.")

        if delegatee:
            input_dict['delegatee_id'] = delegatee.id
        else:
            raise ValidationError("Delegatee user not found in external data.")
        return input_dict

    def lookup_user_external_data(self, item_dict):
        if item_dict.get('id') in [1, 2]:
            return self.env['res.users'].browse(item_dict.get('id'))
        return self.env['res.users'].search([('partner_id.email', '=', item_dict.get('email'))], limit=1)

    @api.model
    def sync_from_doa_server(self):

        url = self.get_endpoint_model_name_url()
        headers = self.get_headers_request()

        params = {
            'domain': "[('state','in',['active','expired'])]",
            'order': 'id asc'
        }
        offset = 0
        total = 1
        row_count = limit = 100
        while row_count == limit:
            params['offset'] = offset
            response = requests.get(url, params=params, headers=headers)
            # ambil last sync datetime
            # todo ambil data last sinc dari config param
            if response.status_code == 404:
                break

            if response.status_code != 200:
                raise UserError(f"Failed to fetch data: {response.status_code} - {response.text}")

            json_data = response.json()
            data = json_data.get("results", [])
            row_count = json_data.get('count', 0)
            _logger.info("Count %s ,Offset %s = Total %s", len(data), offset, row_count)
            for item in data:
                offset = offset + 1
                self.env['external.data.sync'].sync_data_from_external(item, self._name, self.get_doa_app_name())

        _logger.info("Offset %s = total %s", offset, total)

    def cron_sync_from_doa_server(self):
        self.sync_from_doa_server()
