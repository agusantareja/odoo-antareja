import requests
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

class whatsapp_api(models.Model):

    def action_open_logs(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'WhatsApp API Logs',
            'res_model': 'whatsapp.log',
            'view_mode': 'tree,form',
            'domain': [('api_id', '=', self.id)],
            'context': dict(self.env.context),
        }
    log_count = fields.Integer(string='Log Count', compute='_compute_log_count')

    def _compute_log_count(self):
        for rec in self:
            rec.log_count = self.env['whatsapp.log'].search_count([('api_id', '=', rec.id)])
    _name = 'whatsapp.api'

    endpoint = fields.Char('Endpoint')
    header = fields.Text('Header Json')
    param_ids = fields.One2many('whatsapp.api.param','api_id','Body Params')
    active = fields.Boolean(default=True)
    name = fields.Char('Name')

class whatsapp_api_param(models.Model):
    _name = 'whatsapp.api.param'

    name = fields.Char("Key")
    api_id = fields.Many2one('whatsapp.api')