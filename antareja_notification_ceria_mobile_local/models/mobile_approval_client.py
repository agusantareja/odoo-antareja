# -*- coding: utf-8 -*-

import traceback

from odoo import api, fields, models
import json
import requests

from odoo.models import BaseModel


class MobileApprovalClient(models.Model):
    _inherit = "mobile.approval.client"

    def create_request(self, **kwargs):
        self_context = self.with_context(default_state='done')
        record = super(MobileApprovalClient,self_context).create_request(**kwargs)
        record.send()
        return record

    # -------------------------------------------------------
    # SEND
    # -------------------------------------------------------
    def send(self):
        self.ensure_one()
        payload = None
        try:
            payload_dict = self.prepare_send_data()
            payload = json.dumps(payload_dict)
            result= self.env["ceria.mobile.approval"].api_create_request(**payload_dict)
            self.write({
                'response': json.dumps(result),
                'payload':payload,
                'state': 'done'
            })
            return True
        except Exception :
            stack = traceback.format_exc()
            self.write({
                'payload': payload,
                'state': 'error',
                'errors_message': stack,
                'last_error': fields.Datetime.now(),
            })
            return False

    # -------------------------------------------------------
    # SEND PAYLOAD
    # -------------------------------------------------------
    def prepare_send_data(self,**data):
        data_notif = super(MobileApprovalClient,self).prepare_send_data(**data)
        if self.user_ids:
            data_notif['user_ids'] = self.user_ids.ids
        return data_notif
