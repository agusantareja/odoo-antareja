# -*- coding: utf-8 -*-

from odoo import models, fields


class WhatsAppLog(models.Model):
    _name = 'whatsapp.log'
    _description = 'WhatsApp Notification Log'
    _order = 'create_date desc'

    api_id = fields.Many2one('whatsapp.api', string='WhatsApp API', ondelete='set null', index=True)
    res_id = fields.Integer(string='Record ID', readonly=True, index=True)
    model = fields.Char(string='Model Name', readonly=True, index=True)
    record_ref = fields.Reference(string="Record", selection='_referencable_models', compute='_compute_record_ref', readonly=True)
    recipient_partner_id = fields.Many2one('res.partner', string='Recipient', readonly=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ], required=True, default='pending', index=True)
    payload = fields.Text(string='Request Payload', readonly=True)
    response_text = fields.Text(string='API Response', readonly=True)
    failure_reason = fields.Char(readonly=True)

    def _referencable_models(self):
        return [(m.model, m.name) for m in self.env['ir.model'].search([])]

    def _compute_record_ref(self):
        for log in self:
            if log.model and log.res_id:
                log.record_ref = f'{log.model},{log.res_id}'
            else:
                log.record_ref = False
