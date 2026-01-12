# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval
import time
import base64
import mimetypes


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    report_delay_id = fields.Many2one('report.delay')

    def get_report_filename(self, docids, data=None):
        report = self
        report_filename = self.env.context.get('__report_filename')
        if report_filename:
            return report_filename
        report_name = report.name
        if docids:
            obj = self.env[report.model].browse(docids)
            if report.print_report_name and not len(obj) > 1:
                globals_dict = {
                    "object": obj,
                    "time": time,
                    "multi": False,
                    'ctx': self.env.context,
                    'context': self.env.context,
                    'data': data or {},
                }
                report_name = safe_eval(report.print_report_name, globals_dict, )
            # When we print multiple records we still allow a custom
            # filename.
            elif report.print_report_name and len(obj) > 1:
                globals_dict = {
                    "objects": obj,
                    "time": time,
                    "multi": False,
                    'ctx': self.env.context,
                    'context': self.env.context,
                    'data': data or {},
                }
                report_name = safe_eval(report.print_report_name, globals_dict, )

        return report_name

    def report_action(self, docids, data=None, config=True):
        """Return an action of type ir.actions.report.
        :param docids: id/ids/browserecord of the records to print (if not used, pass an empty list)
        :param report_name: Name of the template to generate an action for
        """
        if not data:
            data = {}
        if self.is_delay_generate_store(data):
            return self.create_task_report(docids, data=data).report_action()
        elif self.is_download_form(data):
            return self.report_download_form(docids, data)

        return super(IrActionsReport, self).report_action(docids, data, config)

    def is_delay_generate_store(self, data={}):
        return data.get('report_delay_generate_store') or \
               self.env.context.get('__report_delay_generate_store') or \
               self.report_delay_id

    def is_download_form(self, data={}):
        return False

    def create_task_report(self, docids, data=None):
        return self.env['report.store'].create_task_report(self, docids, data=data, context=self.env.context)

    def report_download_form(self, docids, data=None):
        attachment_dict = self.render_prepare_attachment(docids, data=data)
        wizard_id = self.env['report.download.wizard'].create(
            {'file': attachment_dict.get('datas'), 'filename': attachment_dict.get('name')}
        )
        context = self.env.context
        if docids:
            if isinstance(docids, models.Model):
                active_ids = docids.ids
            elif isinstance(docids, int):
                active_ids = [docids]
            elif isinstance(docids, list):
                active_ids = docids
            context = dict(context, active_ids=active_ids)
        return {
            'view_mode': 'form',
            'res_id': wizard_id.id,
            'name': 'Download',
            'res_model': 'report.download.wizard',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
        }

    def render_prepare_attachment(self, docids, data=None):
        report = self
        content, extension = report.render(docids, data=data)
        filename = "%s.%s" % (report.get_report_filename(docids,data=None), extension)
        mimetype, _ = mimetypes.guess_type(filename)
        content = base64.b64encode(content)
        return {
            'name': filename,
            'type': 'binary',
            'datas': content,
            'mimetype': mimetype,
        }
