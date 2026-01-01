# -*- coding: utf-8 -*-
import logging
from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class MailQueueJob(models.AbstractModel):
    _name = 'mail.queue_job'
    _description = 'Queue Job Email/ Message Mixin for generate'

    @api.model
    def is_module_installed_by_name(self, module_name):
        module = self.env['ir.module.module'].sudo().search([('name', '=', module_name), ('state', '=', 'installed')], limit=1)
        return bool(module)

    @api.model
    def is_module_queue_job_installed(self, ):
        return self.is_module_installed_by_name('queue_job')

    @api.model
    def get_using_queue_for_send_message(self):
        param = self.env['ir.config_parameter'].sudo().get_param('using_queue_for_send_message', 'True')
        return param == 'True' and self.is_module_queue_job_installed()

    # whatsapp
    @api.model
    def send_whatsapp_to_user_ids(self, user_ids, template_id, rec_id, ctx=None):
        """Enqueue email untuk beberapa user_id"""
        self_delay = self
        if self.get_using_queue_for_send_message():
            self_delay = self.with_delay()

        for user_id in user_ids:
            context_object = [('notification_to_user', 'res.users', user_id)]
            self_delay.queue_safe_send_whatsapp(
                template_id, rec_id,ctx=ctx, context_object=context_object)

    @api.model
    def queue_safe_send_whatsapp(self, template_id, rec_id, raise_exception=False, ctx=None,
                                 context_object=None):
        """Job yang dijalankan oleh queue worker"""
        template = self.env['mail.template'].browse(template_id).exists()
        if not template:
            _logger.warning(
                "Template ID %s tidak ditemukan. Email tidak dikirim.", template_id
            )
            if raise_exception:
                raise Exception("Template ID %s tidak ditemukan. Email tidak dikirim." % template_id)
            return
        template.ensure_one()
        ctx = dict(ctx or {})
        rec_model = template.model
        record = self.env[rec_model].browse(rec_id).exists()
        if not record:
            _logger.warning(
                "Record ID %s pada model %s tidak ditemukan. Email tidak dikirim.",
                rec_id, rec_model
            )
            if raise_exception:
                raise Exception(
                    "Record ID %s pada model %s tidak ditemukan. Email tidak dikirim." % (rec_id, rec_model))
            return
        for ctx_object in context_object:
            obj = self.env[ctx_object[1]].browse(ctx_object[2]).exists()
            if obj:
                ctx[ctx_object[0]] = obj
            else:
                _logger.warning(
                    "%s model %s tidak ada untuk id %s",
                    *ctx_object[:3]
                )
        template.with_context(ctx).send_whatsapp(rec_id)

    # mail boot
    @api.model
    def send_mail_bot_to_user_ids(self, user_ids, template_id, rec_id, ctx=None):
        """Enqueue email untuk beberapa user_id"""
        self_delay = self
        if self.get_using_queue_for_send_message():
            self_delay = self.with_delay()

        for user_id in user_ids:
            context_object = [('notification_to_user', 'res.users', user_id)]
            self_delay.queue_safe_send_mail_bot(
                template_id, rec_id,  ctx=ctx, context_object=context_object)

    @api.model
    def queue_safe_send_mail_bot(self, template_id, rec_id, raise_exception=False, ctx=None,
                                 context_object=None):
        """Job yang dijalankan oleh queue worker"""
        template = self.env['mail.template'].browse(template_id).exists()
        if not template:
            _logger.warning(
                "Template ID %s tidak ditemukan. Email tidak dikirim.", template_id
            )
            if raise_exception:
                raise Exception("Template ID %s tidak ditemukan. Email tidak dikirim." % template_id)
            return
        template.ensure_one()
        rec_model = template.model
        record = self.env[rec_model].browse(rec_id).exists()
        if not record:
            _logger.warning(
                "Record ID %s pada model %s tidak ditemukan. Email tidak dikirim.",
                rec_id, rec_model
            )
            if raise_exception:
                raise Exception(
                    "Record ID %s pada model %s tidak ditemukan. Email tidak dikirim." % (rec_id, rec_model))
            return
        ctx = dict(ctx or {})
        for ctx_object in context_object:
            obj = self.env[ctx_object[1]].browse(ctx_object[2]).exists()
            if obj:
                ctx[ctx_object[0]] = obj
            else:
                _logger.warning(
                    "%s model %s tidak ada untuk id %s",
                    *ctx_object[:3]
                )

        mail_bot_to_user = ctx.get('notification_to_user')
        message = self.env['mail.template'].with_context(ctx)._render_template(template.body_html, rec_model, rec_id)
        self.env['mail.channel'].mail_bot_approve(mail_bot_to_user.partner_id, message)

    @api.model
    def send_email_to_user_ids(self, user_ids, template_id, rec_id, ctx=None):
        """Enqueue email untuk beberapa user_id"""
        self_delay = self
        if self.get_using_queue_for_send_message():
            self_delay = self.with_delay()

        for user_id in user_ids:
            context_object = [('notification_to_user', 'res.users', user_id)]
            self_delay.queue_safe_send_email(
                template_id, rec_id,ctx=ctx, context_object=context_object)

    @api.model
    def queue_safe_send_email(self, template_id, rec_id, raise_exception=False, email_values=None,
                              ctx=None, context_object=None):
        """Job yang dijalankan oleh queue worker"""
        template = self.env['mail.template'].browse(template_id).exists()
        if not template:
            _logger.warning(
                "Template ID %s tidak ditemukan. Email tidak dikirim.", template_id
            )
            if raise_exception:
                raise Exception("Template ID %s tidak ditemukan. Email tidak dikirim." % template_id)
            return
        template.ensure_one()
        ctx = dict(ctx or {})
        rec_model = template.model
        record = self.env[rec_model].browse(rec_id).exists()
        if not record:
            _logger.warning(
                "Record ID %s pada model %s tidak ditemukan. Email tidak dikirim.",
                rec_id, rec_model
            )
            if raise_exception:
                raise Exception(
                    "Record ID %s pada model %s tidak ditemukan. Email tidak dikirim." % (rec_id, rec_model))
            return

        for ctx_object in context_object:
            obj = self.env[ctx_object[1]].browse(ctx_object[2]).exists()
            if obj:
                ctx[ctx_object[0]] = obj
            else:
                _logger.warning(
                    "%s model %s tidak ada untuk id %s",
                    *ctx_object[:3]
                )

        try:
            return template.with_context(ctx).send_mail_without_chatter(rec_id, raise_exception=raise_exception,email_values=email_values)
        except Exception as e:
            _logger.exception("Terjadi error di proses email")
            if raise_exception:
                raise e
            return

    def transaction_comment(self,transaction_object,user, message):
        self.env['mail.message'].sudo().create({
            'model': transaction_object._name,
            'res_id': transaction_object.id,
            'message_type': 'comment',
            'author_id': user.partner_id.id,
            'date': fields.Datetime.now(),
            'body': message,
        })
