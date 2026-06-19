# -*- coding: utf-8 -*-

import ast
import json
import logging

import requests

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


class WhatsAppLog(models.Model):
    _inherit = 'whatsapp.log'
    template_id = fields.Many2one('whatsapp.template')
    status = fields.Selection(selection_add=[
        ('cancel', 'Cancel')
    ])
    send_message_post = fields.Boolean("Post Message on Record Chatter", default=True)
    def _referencable_models(self):
        return [(m.model, m.name) for m in self.env['ir.model'].search([])]

    def _compute_record_ref(self):
        for log in self:
            if log.model and log.res_id:
                log.record_ref = f'{log.model},{log.res_id}'
            else:
                log.record_ref = False

    def send(self):
        self.ensure_one()
        if self.api_id:
            api_server = self.api_id
        else:
            api_server = self.api_id.search([],limit=1)

        # def build_headers():
        #     try:
        #         header = ast.literal_eval(api_server.header)
        #     except Exception as e:
        #         _logger.error("Error parsing headers for WhatsApp API ID %s: %s", api_server.id, e)
        #         header = {}
        #     return header

        if not api_server:
            self.sudo().write({
                'status': 'failed',
                'failure_reason': "No API Service. Please check config WhatsApp API Client",
            })
            return
        headers  = api_server.get_request_headers()
        payload = json.loads(self.payload)
        url = api_server.endpoint
        try:
            response = requests.post(
                url=url,
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            if self.res_id and self.model and self.send_message_post:
                record = self.env[self.model].browse(self.res_id)
                if record and have_method(record, 'message_post'):
                    if self.template_id:
                        record.sudo().message_post(
                            body=_(
                                'WhatsApp message is sent to %s via template %s'
                                % (
                                    self.recipient_partner_id.name,
                                    self.template_id.name,
                                )
                            ),
                            author_id=1,  # OdooBot partner_id is always 1
                        )
                    else:
                        record.sudo().message_post(
                            body=_(
                                'WhatsApp message is sent to %s'
                                % (self.recipient_partner_id.name,)
                            ),
                            author_id=1,  # OdooBot partner_id is always 1
                        )
            self.sudo().write({
                'status': 'sent',
                'response_text': response.text,
            })
        except requests.RequestException as e:
            _logger.error("Failed to send WhatsApp message ID [%s]: %s", self.id, e)
            self.sudo().write({
                'status': 'failed',
                'failure_reason': str(e),
                'response_text': getattr(e.response, 'text', ''),
            })

    def cron_send(self):
        pending_logs = self.search([('status', '=', 'pending')], limit=1000)
        for log in pending_logs:
            log.send()

    def cancel(self):
        self.write({
            'status': 'cancel',
        })

    def mark_pending(self):
        self.write({
            'status': 'pending',
        })
