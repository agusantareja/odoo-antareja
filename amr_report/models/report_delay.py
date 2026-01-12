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
    _description = 'Report Delay'

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
