# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).

from odoo import models, fields
import logging
import time
from odoo.tools.safe_eval import safe_eval

try:
    import simplejson as json
except ImportError:
    import json

_logger = logging.getLogger(__name__)


class ReportDelay(models.Model):
    _name = 'report.delay'
    _description = 'Report Async'

    name = fields.Char('Name')
    model_id = fields.Many2one('ir.model')
    model = fields.Char(related='model_id.model')

    next_action_id = fields.Many2one(
        'ir.actions.server',
        help="Execute next action when using generate store.",
        domain=[('usage', '=', 'ir_actions_server')]
    )
    send_email_template_id = fields.Many2one(
        'mail.template',
    )
    send_email_to_partner = fields.Char(
        string="Send email to partner",
        default=False,
        help="Send when data set send_email_to_partner with partner",
    )
    report_in_email_attachment = fields.Boolean(
        string="In Attachment",
        default=False,
        help="If checked, the report send in Attachment.",
    )

    def get_send_email_to_partners(self, docids, user):
        report = self
        partners = None
        if docids:
            obj = self.env[report.model].browse(docids)
            if report.send_email_to_partner and not len(obj) > 1:
                partners = safe_eval(
                    report.send_email_to_partner,
                    {"object": obj, "time": time, "multi": False, "user": user or self.env.user},
                )

            elif report.send_email_to_partner and len(obj) > 1:
                partners = safe_eval(
                    report.send_email_to_partner,
                    {"objects": obj, "time": time, "multi": True, "user": user or self.env.user},
                )
        return partners

    def send_email(self, doc_ids=None, attachment=None, email_values=None):
        if not self:
            return

        template = self.send_email_template_id or self.env.ref("amr_report.report_delivery")
        if self.report_in_email_attachment:
            email_values['attachment_ids'] = attachment.ids
        rec_id = None
        if 'ir.attachment' == template.model:
            rec_id = attachment.id
        elif 'report.store' == template.model:
            rec_id = self.id
        elif doc_ids and self.model == template.model:
            if isinstance(doc_ids, int):
                rec_id = doc_ids
            elif isinstance(doc_ids, list) and len(doc_ids) == 1:
                rec_id = doc_ids[0]

        rec_id and template.send_mail(
            rec_id,
            email_values=email_values,
            notif_layout="mail.mail_notification_light",
            force_send=False
        )

    def next_action(self,parameter):
        context = parameter.get('context') or {}
        context['data'] = parameter.get('data') or {}
        self.next_action_id and self.next_action_id.with_context(context).run()
