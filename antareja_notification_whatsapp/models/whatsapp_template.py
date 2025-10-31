# -*- coding: utf-8 -*-

import json
import logging

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

class WhatsappTemplate(models.Model):
    _inherit = 'whatsapp.template'
    model = fields.Char(related='model_id.model')

    def custom_render(self, template_str, context):
        if isinstance(context,dict) and 'user' not in context:
            context = dict(context,user= self.env.user)
        return super(WhatsappTemplate,self).custom_render(template_str, context)

    def send_whatsapp(self, rec_id, force_send=False):
        _logger.info("Sending WhatsApp message using template: %s", self.name)
        self.ensure_one()
        self = self.sudo()
        WhatsAppLog = self.env['whatsapp.log']
        ModelObject = self.env[self.model]
        rec = ModelObject.browse(rec_id)
        context = {'object': rec, 'obj': rec, 'ctx': self.env.context}
        partners_expr = self.recipient or ''
        partners_val = self.custom_render(partners_expr, context)
        try:
            partners = safe_eval(partners_val, context)
        except Exception as e:
            _logger.error("Error evaluating recipient '%s' for record ID %s: %s", self.recipient, rec.id, e)
            return
        results = WhatsAppLog.browse()
        for partner in partners:
            phone = self._format_phone_number(partner.mobile or partner.phone)
            if not phone:
                _logger.warning("Invalid phone number for partner ID %s", getattr(partner, 'id', 'n/a'))
                return
            payload = {}
            for param in self.body_param_ids:
                try:
                    payload[param.key] = self.render_param_value(param, rec, partner=partner, phone=phone)
                except Exception as e:
                    _logger.error("Error rendering parameter '%s' for record ID %s: %s", param.key, rec.id, e)
                    return
            log_vals = {
                'api_id': self.whatsapp_api_id.id,
                'model': rec._name,
                'res_id': rec.id,
                'recipient_partner_id':partner.id,
                'payload': json.dumps(payload),
                'status': 'pending',
            }
            result = WhatsAppLog.create(log_vals)
            if force_send:
                result.send()
            results |=  result
        return results
