# -*- coding: utf-8 -*-

import ast
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
import random
import re
import requests

_logger = logging.getLogger(__name__)


class WhatsAppTemplate(models.Model):
    _name = 'whatsapp.template'
    _sql_constraints = [
        ('unique_template_name_model', 'unique(name, model_id)', 'The combination of WhatsApp template name and model must be unique.')
    ]

    recipient_info = fields.Html(string="Recipient Info", compute="_compute_recipient_info", store=False)
    body_param_info = fields.Html(string="Parameter Info", compute="_compute_body_param_info", store=False)
    name = fields.Char('Name')
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade')
    recipient = fields.Char("Recipient", help="Expression to determine the recipient partner(s). Use ${...} expressions. Example: ${[partner]} or ${[obj.partner_id]}.")
    body_param_ids = fields.One2many('whatsapp.template.param','template_id')
    whatsapp_api_id = fields.Many2one('whatsapp.api','WhatsApp API')

    def _register_hook(self):
        super()._register_hook()
        # Use a delayed call to ensure all models are loaded
        self._inject_send_whatsapp_method()

    @api.depends('recipient')
    def _compute_recipient_info(self):
        info = (
            '<div class="alert alert-info o_form_label" style="margin-bottom:8px">'
            'Use a Python expression that returns a <b>list or recordset of res.partner</b>.'
            '<br/>Example: <code>obj.partner_ids</code> or <code>obj.user_ids.mapped(\'partner_id\')</code>'
            '<br/>You can use <code>obj</code> (the current record) and <code>ctx</code> (the Odoo context).'
            '</div>'
        )
        for rec in self:
            rec.recipient_info = info

    @api.depends('body_param_ids.type')
    def _compute_body_param_info(self):
        info = (
            '<div class="alert alert-info o_form_label" style="margin-bottom:8px">'
            'Use <code>${}</code> expressions, similar to Jinja, for any parameter with type <b>Expression</b>.'
            '<br/>Example: <code>${obj.name}</code> or <code>${partner.phone}</code>'
            '<br/><br/><b>Available variables:</b>'
            '<ul style="margin-bottom:0">'
            '<li><code>obj</code>: The current record (same as <code>object</code>)</li>'
            '<li><code>partner</code>: The recipient partner (from the recipient expression)</li>'
            '<li><code>phone</code>: The recipient phone number (if available)</li>'
            '<li><code>ctx</code>: The Odoo context</li>'
            '</ul>'
            '</div>'
        )
        for rec in self:
            rec.body_param_info = info if any(p.type == 'record' for p in rec.body_param_ids) else ''

    def custom_render(self, template_str, context):
        pattern = re.compile(r'\${(.*?)}')
        def replacer(match):
            expr = match.group(1)
            try:
                return str(safe_eval(expr, context))
            except Exception as e:
                _logger.error("Error rendering expression '%s': %s", expr, e)
                return ''
        return pattern.sub(replacer, template_str)
    
    def render_param_value(self, param, rec, partner=None, phone=None):
        """
        Render the value of a param using custom_render for dynamic values.
        For 'record' type, fallback to safe_eval for backward compatibility.
        """
        context = {'object': rec, 'partner': partner, 'phone': phone, 'obj': rec, 'ctx': self.env.context}
        if param.type == 'fix':
            return param.value
        elif param.type == 'record':
            if '${' in param.value:
                return self.custom_render(param.value, context)
            else:
                return safe_eval(param.value, context)
        elif param.type == 'random_int':
            return random.randint(0, int(param.value) if param.value.isdigit() else 1000)
        return None

    @api.onchange('whatsapp_api_id')
    def update_body_param(self):
        self.body_param_ids = False
        self.body_param_ids = [(0,0,{'key':x.name}) for x in self.whatsapp_api_id.param_ids]

    def _format_phone_number(self, phone):
        if not phone:
            return False
        
        phone = re.sub(r'\D', '', phone)
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif phone.startswith('62'):
            pass
        elif not phone.startswith('62'):
            phone = '62' + phone

        return phone

    def send(self, records):
        _logger.info("Sending WhatsApp message using template: %s", self.name)
        self.ensure_one()
        self = self.sudo()
        WhatsAppLog = self.env['whatsapp.log']
        for rec in records:
            context = {'object': rec, 'obj': rec, 'ctx': self.env.context}
            partners_expr = self.recipient or ''
            partners_val = self.custom_render(partners_expr, context)
            try:
                partners = safe_eval(partners_val, context)
            except Exception as e:
                _logger.error("Error evaluating recipient '%s' for record ID %s: %s", self.recipient, rec.id, e)
                continue
            for partner in partners:
                phone = self._format_phone_number(partner.mobile or partner.phone)
                if not phone:
                    _logger.warning("Invalid phone number for partner ID %s", getattr(partner, 'id', 'n/a'))
                    continue
                payload = {}
                for param in self.body_param_ids:
                    try:
                        payload[param.key] = self.render_param_value(param, rec, partner=partner, phone=phone)
                    except Exception as e:
                        _logger.error("Error rendering parameter '%s' for record ID %s: %s", param.key, rec.id, e)
                        continue
                try:
                    headers = ast.literal_eval(self.whatsapp_api_id.header)
                except Exception as e:
                    _logger.error("Error parsing headers for WhatsApp API ID %s: %s", self.whatsapp_api_id.id, e)
                    headers = {}
                log_vals = {
                    'api_id': self.whatsapp_api_id.id,
                    'model': rec._name,
                    'res_id': rec.id,
                    'recipient_partner_id': getattr(partner, 'id', False),
                    'payload': json.dumps(payload),
                    'status': 'pending',
                }
                try:
                    response = requests.post(
                        url=self.whatsapp_api_id.endpoint,
                        headers=headers,
                        json=payload,
                        timeout=10
                    )
                    response.raise_for_status()
                    rec.sudo().message_post(
                        body=_('WhatsApp message is sent to %s via template %s' % (getattr(partner, 'name', ''), self.name)),
                        author_id=1  # OdooBot partner_id is always 1
                    )
                    _logger.info("WhatsApp message sent to %s via template %s", phone, self.name)
                    log_vals.update({
                        'status': 'sent',
                        'response_text': response.text,
                    })
                except requests.RequestException as e:
                    raise ValidationError(_('Connection lost, please try again.'))
                    # _logger.error("Failed to send WhatsApp message to %s via template %s: %s", phone, rec.name, e)
                    # log_vals.update({
                    #     'status': 'failed',
                    #     'failure_reason': str(e),
                    #     'response_text': getattr(e.response, 'text', ''),
                    # })
                WhatsAppLog.create(log_vals)

    @api.model
    def get_template_by_name(self, name):
        """
        Fetch a WhatsApp template record by its name.
        :param name: The name of the WhatsApp template to fetch.
        :return: A recordset of the WhatsApp template or an empty recordset if not found.
        """
        return self.search([('name', '=', name)], limit=1)

    @api.model
    def _inject_send_whatsapp_method(self):
        """
        Dynamically inject the `send_whatsapp_by_template` method into models
        specified in the `model_id` field of WhatsApp templates.
        """
        try:
            templates = self.search([])
            processed_models = set()
            
            for template in templates:
                model_name = template.model_id.model
                if model_name in processed_models:
                    continue  # Skip if already processed
                processed_models.add(model_name)
                
                try:
                    # Check if model exists and is available
                    if model_name not in self.env:
                        _logger.warning("Model %s not found in registry", model_name)
                        continue
                        
                    model_cls = self.env[model_name].__class__
                    
                    # Always re-inject to handle imports/updates
                    def send_whatsapp_by_template(self, template_name):
                        template = self.env['whatsapp.template'].get_template_by_name(template_name)
                        if not template:
                            raise UserError(_(
                                'WhatsApp template "%(template)s" not found.',
                                template=template_name
                            ))
                        template.send(self)

                    send_whatsapp_by_template.__doc__ = (
                        "Send WhatsApp messages using the specified template.\n"
                        "\n"
                        "Args:\n"
                        "    template_name (str): The name of the WhatsApp template to use."
                    )

                    setattr(model_cls, 'send_whatsapp_by_template', send_whatsapp_by_template)
                    _logger.info("Injected send_whatsapp_by_template method to model: %s", model_name)
                    
                except Exception as e:
                    _logger.warning("Could not inject send_whatsapp_by_template to model %s: %s", model_name, e)
                    
        except Exception as e:
            _logger.error("Error during method injection: %s", e)

    @api.model
    def create(self, vals):
        template = super(WhatsAppTemplate, self).create(vals)
        self._inject_send_whatsapp_method()
        return template

    def write(self, vals):
        res = super(WhatsAppTemplate, self).write(vals)
        self._inject_send_whatsapp_method()
        return res

class WhatsAppTemplateParam(models.Model):
    _name = 'whatsapp.template.param'

    key = fields.Char('Key')
    value = fields.Text('Value')
    type = fields.Selection([
        ('fix', 'Fixed Value'),
        ('record', 'Expression'),
        ('random_int', 'Random Integer'),
    ], 'Type', default="fix")
    template_id = fields.Many2one('whatsapp.template')
