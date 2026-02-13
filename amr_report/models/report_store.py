# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).

from datetime import timedelta, datetime, date
from odoo import models, fields
import logging
import traceback

try:
    import simplejson as json
except ImportError:
    import json

_logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, models.Model):
            return {
                '___model_name': obj._name,
                '___ids': obj.ids,
                '___uid': obj._uid
            }
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8")
        if isinstance(obj, datetime):
            return fields.Datetime.to_string(obj)
        if isinstance(obj, date):
            return fields.Date.to_string(obj)
        return json.JSONEncoder.default(self, obj)


class ReportDownloadMixin(models.AbstractModel):
    _name = 'report.download.mixin'
    _description = 'Report Download Mixin'

    file = fields.Binary('Report', readonly=True)
    filename = fields.Char(readonly=True)


class ReportDownloadAttachmentMixin(models.AbstractModel):
    _name = 'report.download.attachment.mixin'
    _inherit = 'report.download.mixin'
    _description = 'Report Download Attachment Mixin'

    attachment_id = fields.Many2one('ir.attachment', "Attachment", ondelete='set null')
    file = fields.Binary(related='attachment_id.datas')
    filename = fields.Char(related='attachment_id.name')


class ReportGenerateStoreWizardMixin(models.AbstractModel):
    _name = 'report.store.wizard.mixin'
    _description = 'Report Generate Store Wizard Mixin'

    report_id = fields.Many2one('ir.actions.report')


class ReportStore(models.Model):
    _name = 'report.store'
    _inherit = 'report.download.attachment.mixin'
    _description = 'Report Async Store'

    name = fields.Char('Name')
    user_id = fields.Many2one(
        'res.users',
        string='User',
        help="User generate dan owner report",
        default=lambda self: self.env.user.id,
        readonly=True
    )
    recipient_ids = fields.Many2many(
        'res.partner',
        string='Email Recipient',
        help="Send Email to Partner Recipient",
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help="Company generate  report",
        default=lambda self: self.env.company.id,
        readonly=True
    )
    state = fields.Selection([
        ('prepare', 'Prepare'),
        ('processing', 'Processing'),
        ('error', 'Error'),
        ('done', 'Done'),
    ], default='prepare')
    executor = fields.Selection([
        ('cron', 'Cron'),
        ('queue', 'Queue Job'),
    ], default='cron')
    error_message = fields.Char()
    error_trace = fields.Text()
    last_call = fields.Datetime()
    next_call = fields.Datetime(default=lambda self: fields.Datetime.now() + timedelta(seconds=10))
    send_email_report = fields.Boolean(
        string="Send Email",
        help="Send email with link to report, when it is ready",
        readonly=True
    )
    next_action = fields.Boolean(
        string="Next Action",
        help="Execute Next Action when done generate report",
        readonly=True
    )
    start_render = fields.Datetime(
        readonly=True
    )
    generated_at = fields.Datetime(
        readonly=True
    )
    parameter_json = fields.Text('Parameter JSON')
    report_id = fields.Many2one('ir.actions.report')
    report_delay_id = fields.Many2one('report.delay', related='report_id.report_delay_id',store=True)

    def create_task_report(self, report, docids, data=None, context=None):
        context = context or self.env.context
        if docids:
            if isinstance(docids, models.Model):
                active_ids = docids.ids
                docids = docids.ids
            elif isinstance(docids, int):
                active_ids = [docids]
            elif isinstance(docids, list):
                active_ids = docids
            context = dict(context, active_ids=active_ids)

        '__report_delay_generate_store' in context and context.pop('__report_delay_generate_store')
        # filter_load_data
        parameter_json = {
            'docids': docids,
            'data': data,
            'context': context,
        }
        vals = {
            'name': report.name,
            'report_id': report.id,
            'parameter_json': json.dumps(parameter_json, cls=JSONEncoder),
        }
        partners = report.report_delay_id.get_send_email_to_partners(docids, self.env.user)
        if partners:
            if isinstance(partners, int):
                partners = [partners]
            vals.update(
                recipient_ids=partners
            )

        return self.create([vals])[0]

    def cron_render_report(self):
        records = self.search([
            ('state', '=', 'prepare'),
            ('next_call', '<=', fields.Datetime.now())
        ], limit=100)

        for record in records:
            record.render_report()

    def action_generate_report(self):
        self.render_report()
        if self.state == 'done':
            action = self.report_action()
            action['view_id'] = self.env.ref('amr_report.view_report_download_wizard').id
            action['target'] = 'new'
            return action

    def report_action(self):
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'name': 'Generate Report Store',
            'res_model': 'report.store',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'create': False, 'update': False}
        }

    def action_response(self):
        view_id = self.env.ref("amr_report.view_report_form_download").id
        return {
            'view_id': view_id,
            'view_mode': 'form',
            'res_id': self.id,
            'name': 'Download Report Store',
            'res_model': 'report.store',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'create': False, 'update': False}
        }

    def action_open_attachment(self):
        view_id = self.env.ref("amr_report.view_report_form_download").id
        return {
            'view_id': view_id,
            'view_mode': 'form',
            'res_id': self.id,
            'name': 'Generate Report Store',
            'res_model': 'report.store',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'create': False, 'update': False}
        }

    def render_report(self):
        self.ensure_one()
        self.write({
            'state': 'processing',
            'last_call': fields.Datetime.now(),
        })
        self.env.cr.commit()
        try:
            self._render_report()
            self.write({'state': 'done', 'error_message': None, 'generated_at': fields.Datetime.now()})
        except Exception as e:
            self.env.cr.rollback()
            _logger.error(f"Error generating report for record ID {self.id}: {str(e)}", exc_info=True)
            error = traceback.format_exc()
            self.write({
                'state': 'error',
                'error_message': f"Error generating report for record ID {self.id}: {str(e)}",
                'error_trace': error
            })
        finally:
            self.env.cr.commit()

    def get_parameter(self):
        def object_hook(obj):
            """
            '___model_name': obj._name,
            '___ids': obj.ids,
            '___uid': obj._uid
            """
            if '___model_name' in obj:
                ids = obj.get('___ids', [])
                uid = obj.get('___uid')
                model = self.env[obj['___model_name']]
                if uid != self._uid:
                    model = model.with_user(uid)
                return model.browse(ids)
            return obj

        return json.loads(self.parameter_json, object_hook=object_hook)

    def _render_report(self):
        parameters = self.get_parameter()
        data = parameters.get('data') or {}
        docids = parameters.get('docids') or []
        context = parameters.get('context')
        if self.company_id:
            context['force_company'] = self.company_id.id
        if self.user_id.company_ids:
            context['allowed_company_ids'] = self.user_id.company_ids.ids
        env = self.report_id.with_context(context).env
        if self.user_id and self._uid != self.user_id.id:
            env = env.with_user(self.user_id)
        report = self.report_id.with_env(env)
        attachment_dict = report.render_prepare_attachment(docids, data=data)
        attachment_dict.update(
            res_model=self._name,
            res_id=self.id
        )
        self.attachment_id = self.env['ir.attachment'].sudo().create(attachment_dict)
        self._send_email()
        self._next_action(parameters)

    def action_send_email(self):
        parameters = self.get_parameter()
        docids = parameters.get('docids') or []
        self._send_email(docids,raise_exception=True)


    def action_next_action(self):
        parameters = self.get_parameter()
        self._next_action(parameters, raise_exception=True)


    def _send_email(self, docids=None,raise_exception=False):
        if self.recipient_ids:
            try:
                email_values = {'recipient_ids': self.recipient_ids.ids}
                self.report_id.report_delay_id.send_email(docids,self.attachment_id,email_values=email_values)
                self.send_email_report=False
            except Exception:
                if raise_exception:
                    raise
                self.send_email_report=True

    def _next_action(self, parameters,raise_exception=False):
        try:
            self.report_delay_id.next_action(parameters)
            self.next_action = False
        except Exception:
            if raise_exception:
                raise
            self.next_action = True
