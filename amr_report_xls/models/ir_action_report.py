# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReportAction(models.Model):
    _inherit = "ir.actions.report"

    report_type = fields.Selection(
        selection_add=[("xls", "XLS")],
    )

    def is_download_form(self, data={}):
        if self.report_type == 'xls':
            return True
        return super(ReportAction, self).is_download_form(data=data)

    @api.model
    def render_xls(self, docids, data):
        report_model_name = "report.%s" % self.report_name
        report_model = self.env.get(report_model_name)
        if report_model is None:
            raise UserError(_("%s model was not found") % report_model_name)
        return report_model.with_context(active_model=self.model).create_xls_report(docids, data)
