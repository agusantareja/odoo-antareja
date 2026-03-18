# -*- coding: utf-8 -*-
from odoo import models, fields, api

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class MailTemplate(models.Model):
    _inherit = "mail.template"

    # whatsapp_number = fields.Char('Whatsapp Number')
    # whatsapp_ref = fields.Char('Whatsapp', default='${object.name}')

    def send_whatsapp(self, res_id, force_send=False):
        """ Generates a new whatsapp. Template is rendered on record given by
        res_id and model coming from template.

        :param int res_id: id of the record to render the template
        :param bool force_send: send email immediately; otherwise use the mail
            queue (recommended);
        """
        self.ensure_one()
        Whatsapp = self.env["send_message.whatsapp"]
        values = self.generate_email(res_id, fields=['email_to', 'subject', 'body_html'])
        return Whatsapp.send_message_whatsapp(
            values['body'], values['email_to'], ref=values['subject'], force_send=force_send)

    def send_mail_without_chatter(self,res_id, force_send=False, raise_exception=False, email_values=None,
                                  notif_layout=False):
        """
        this method copy form
        Generates a new mail.mail. Template is rendered on record given by
        res_id and model coming from template.

        :param int res_id: id of the record to render the template
        :param bool force_send: send email immediately; otherwise use the mail
            queue (recommended);
        :param dict email_values: update generated mail with those values to further
            customize the mail;
        :param str notif_layout: optional notification layout to encapsulate the
            generated email;
        :returns: id of the mail.mail that was created """
        self.ensure_one()
        Mail = self.env['mail.mail']
        Attachment = self.env['ir.attachment']  # TDE FIXME: should remove default_type from context

        # create a mail_mail based on values, without attachments
        values = self.generate_email(res_id)
        values['recipient_ids'] = [(4, pid) for pid in values.get('partner_ids', list())]
        values['attachment_ids'] = [(4, aid) for aid in values.get('attachment_ids', list())]
        values.update(email_values or {})
        attachment_ids = values.pop('attachment_ids', [])
        attachments = values.pop('attachments', [])
        # add a protection against void email_from
        if 'email_from' in values and not values.get('email_from'):
            values.pop('email_from')
        # encapsulate body
        if notif_layout and values['body_html']:
            try:
                template = self.env.ref(notif_layout, raise_if_not_found=True)
            except ValueError:
                _logger.warning(
                    'QWeb template %s not found when sending template %s. Sending without layouting.' % (
                        notif_layout, self.name))
            else:
                record = self.env[self.model].browse(res_id)
                lang = self._render_template(self.lang, self.model, res_id)
                model = self.env['ir.model']._get(record._name)
                if lang:
                    template = template.with_context(lang=lang)
                    model = model.with_context(lang=lang)
                template_ctx = {
                    'message': self.env['mail.message'].sudo().new(
                        dict(body=values['body_html'], record_name=record.display_name)),
                    'model_description': model.display_name,
                    'company': 'company_id' in record and record['company_id'] or self.env.company,
                    'record': record,
                }
                body = template.render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                values['body_html'] = self.env['mail.thread']._replace_local_links(body)

        # mencegah masuk chater untuk send
        values.pop('res_id', None)
        mail = Mail.create(values)

        # manage attachments
        for attachment in attachments:
            attachment_data = {
                'name': attachment[0],
                'datas': attachment[1],
                'type': 'binary',
                'res_model': 'mail.message',
                'res_id': mail.mail_message_id.id,
            }
            attachment_ids.append((4, Attachment.create(attachment_data).id))
        if attachment_ids:
            mail.write({'attachment_ids': attachment_ids})

        if force_send:
            mail.send(raise_exception=raise_exception)
        return mail.id  # TDE CLEANME: return mail + api.returns ?
