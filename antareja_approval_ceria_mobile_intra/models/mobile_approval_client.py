# -*- coding: utf-8 -*-

import traceback

from odoo import api, fields, models
import json
import requests

from odoo.models import BaseModel


class MobileApprovalClient(models.Model):
    _name = "mobile.approval.client"
    _inherit = 'approval.transaction.able.mixin'
    # _rec_name = 'title'
    _order = 'id desc'

    name = fields.Char()

    state = fields.Selection([
        ('outgoing', 'Outgoing'),
        ('error', 'Error'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], default='outgoing')

    request_type = fields.Selection(
        [('register_approval', 'Register Approval'),
         ('unregister_approval', 'Un-Register Approval'),
         ('unregister_user_approval', 'Un-Register User Approval'),],
        default='unregister_approval'
    )
    user_ids = fields.Many2many('res.users')
    url = fields.Char()
    number = fields.Char("Document Number")
    document = fields.Char("Document Type")
    originator_name = fields.Char("Originator Name")
    approval_task_line_model_name = fields.Char()
    approval_task_line_id = fields.Integer()

    payload = fields.Text()
    errors_message = fields.Text()
    last_error = fields.Datetime()
    response = fields.Text()

    def get_application_name(self):
        return self.env['ir.config_parameter'].sudo().get_param('antareja.application_name')

    @api.model
    def get_mobile_approval_path(self):
        return "/api/intra/mobile/approval"

    def get_server_auth(self):
        server_auth_id = int(
            self.env['ir.config_parameter']
            .sudo()
            .get_param('antareja_approval_ceria_mobile_intra.mobile_approval_server_auth_id', 0)
        )

        return self.env['application.server.auth'].browse(server_auth_id)

    def create_request(self, **kwargs):
        data = {}

        def to_list_for_m2m(values):
            if isinstance(values, BaseModel):
                return values.ids
            elif isinstance(values, list):
                return values
            return []

        for key in ['name', 'request_type',
                    'number','document','originator_name', 'url',
                    'transaction_model_name', 'transaction_id',
                    'approval_task_line_model_name', 'approval_task_line_id']:
            value = kwargs.get(key, None)
            if value is not None:
                data[key] = value

        if 'user_ids' in kwargs:
            objects = kwargs.get('user_ids')
            if objects:
                data['user_ids'] = [(6, 0, to_list_for_m2m(objects))]
        else:
            data['user_ids'] = []

        return self.create([data])[0]

    # -------------------------------------------------------
    # SEND
    # -------------------------------------------------------
    # def get_endpoint_approval(self):
    #     config = self.env['ir.config_parameter'].sudo()
    #     base_url = config.get_param('antareja_approval_ceria_mobile_intra.mobile_approval_endpoint')
    #     url = f"{base_url}/api/intra/mobile/approval"
    #     headers = {
    #         "token": config.get_param('antareja_approval_ceria_mobile_intra.mobile_approval_token'),
    #         "Accept": "application/json"
    #     }
    #     return url,headers

    def send(self):
        self.ensure_one()
        payload = None
        try:
            payload_dict = self.prepare_send_data()
            payload = json.dumps(payload_dict)
            server_auth = self.get_server_auth()
            with server_auth.create_session() as s:
                response = s.rest_post(path=self.get_mobile_approval_path(), data=json.dumps(payload))
                response.raise_for_status()
                self.write({
                    'response': response.text,
                    'payload': payload,
                    'state': 'done'
                })
                return True
        except Exception:
            stack = traceback.format_exc()
            self.write({
                'payload': payload,
                'state': 'error',
                'errors_message': stack,
                'last_error': fields.Datetime.now(),
            })
            return False

    def cron_send(self):
        records = self.search([('state', '=', 'outgoing')],limit=1000)
        for rec in records:
            rec.send()

    def mark_outgoing(self):
        self.write({'state': 'outgoing'})

    def cancel(self):
        self.write({'state': 'cancel'})

    # -------------------------------------------------------
    # SEND PAYLOAD
    # -------------------------------------------------------
    def prepare_send_data(self,**data):
        data_notif = {k: str(v) for k, v in data.items()}
        data_notif.update(
            {
                "request_type": self.request_type,
                "source_application": self.get_application_name(),
                "source_model": self.transaction_model_name or "",
                "source_res_id": self.transaction_id,
                "source_approval_model": self.approval_task_line_model_name or "",
                "source_approval_res_id": self.approval_task_line_id,
                "source_number": self.number,
                "source_document": self.document,
                "source_originator_name": self.originator_name,
                "source_url": self.url,
                "request_datetime":fields.Datetime.to_string(self.create_date)
            }
        )
        if self.user_ids:
            data_notif['user_list'] = [user.partner_id.email for user in self.user_ids if user.partner_id.email]
        return data_notif
