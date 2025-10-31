# -*- coding: utf-8 -*-

from odoo import fields, models
import logging
_logger = logging.getLogger(__name__)

def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))

class NotificationTemplate(models.Model):
    _name = "notification.template"
    _description = "Notification Template"

    active = fields.Boolean(default=True)
    name = fields.Char("Notification")
    model = fields.Char("Model")
    scope = fields.Char("Scope", default="INTRA")
    template_email = fields.Many2one('mail.template')
    template_wa = fields.Many2one('mail.template')
    template_chatter = fields.Many2one('mail.template')
    template_comment = fields.Many2one(
        'mail.template',
        help='Comment Post'
    )

    def get_test_email(self):
        return self.env['ir.config_parameter'].sudo().get_param('send_message_cron.test_email') or "False"

    def get_test_wa(self):
        return self.env['ir.config_parameter'].sudo().get_param('notif_wa_test') or "False"

    def get_wa_scope_default(self):
        return self.env['ir.config_parameter'].sudo().get_param('antareja_notification.scope_default')

    def send_notification_to_users(self,users,res_id,**kwargs):
        if not users or not res_id:
            return
        self.ensure_one()
        for notification_to_user in users:
            notif_log = self.send_notification_to_user(notification_to_user, res_id)
            if notif_log :
                notif_log['res_id'] = res_id
                notif_log['receiver_id']=notification_to_user.id
                notif_log['notification_template_id']=self.id
                notif_log['transaction_id'] = kwargs.get('transaction_id')
                notif_log['transaction_model_name'] = kwargs.get('transaction_model_name')
                self.env['notification.log'].create(notif_log)

        self.send_comment_post(res_id,**kwargs)

    def send_notification_to_user(self, notification_to_user, res_id):
        notif_log = {}
        result = self.send_notification_to_user_email(notification_to_user, res_id)
        if result:
            notif_log['mail_id'] = result.id
            notif_log['mail_model'] = result._name

        result = self.send_notification_to_user_wa(notification_to_user, res_id)
        if result:
            notif_log['send_message_id'] = result.id
            notif_log['send_message_model'] = result._name

        result = self.send_notification_to_user_chatter(notification_to_user, res_id)
        if result:
            notif_log['chat_message_id'] = result.id
            notif_log['chat_message_model'] = result._name
        return notif_log

    def send_notification_to_user_email(self, notification_to_user, res_id):
        if not notification_to_user or not res_id:
            return

        self.ensure_one()
        if self.template_email:
            values = self.template_email.with_context(notification_to_user=notification_to_user).generate_email(res_id)
            values['recipient_ids'] = [(4, pid) for pid in values.get('partner_ids', list())]
            values['attachment_ids'] = [(4, aid) for aid in values.get('attachment_ids', list())]
            values.pop('partner_ids', None)
            # supaya tidak di tulis di chatter res_id di hapus
            if 'res_id' in values:
                values.pop('res_id')
            test_email = self.get_test_email()
            if 'False' != test_email:
                _logger.info(
                    f"TO: {values.get('email_to')} CC: {values.get('email_cc')} RR: {values.get('recipient_ids')} --> {test_email}")
                values['email_to'] = test_email
                if 'email_cc' in values:
                    values.pop('email_cc')
                if 'recipient_ids' in values:
                    values.pop('recipient_ids')
                # set false untuk testing mode untuk meyakinkan bahwa telah  di kirim
                values['auto_delete'] = False

            return self.env['mail.mail'].sudo().create(values)

        return None

    def send_notification_to_user_wa(self, notification_to_user, res_id):
        if not notification_to_user or not res_id:
            return
        self.ensure_one()
        if self.template_wa:
            values = self.template_wa.sudo().with_context(notification_to_user=notification_to_user).generate_email(
                res_id)
            message_wa = values['body_html']
            ref = values['subject']
            return self.env['send_message.email'].sudo().create({
                'receiver': notification_to_user.id,
                'ref': ref,
                'message': message_wa,
                'is_send': True,
                'is_send_wa': False,
            })

        return None

    def send_notification_to_user_chatter(self,notification_to_user,res_id):
        if not notification_to_user or not res_id:
            return
        self.ensure_one()
        if self.template_chatter:
            values = self.template_chatter.with_context(notification_to_user=notification_to_user).generate_email(res_id)
            message=values['body_html']
            return notification_to_user.send_odoobot_message(message)

        return None

    def send_comment_post(self,res_id,**kwargs):
        if not  not res_id:
            return
        self.ensure_one()
        if self.template_comment :
            transaction_id = kwargs.get('transaction_id')
            transaction_model_name = kwargs.get('transaction_model_name')
            if transaction_id and transaction_model_name:
                rec = self.env[transaction_model_name].browse(transaction_id)
                odoobot_id = self.env['ir.model.data']._xmlid_to_res_id("base.partner_root")
                if rec and have_method(rec, 'message_post'):
                    values = self.template_comment.generate_email(res_id, ['body_html'])
                    message = values['body_html']
                    return rec.message_post(
                        body=message,
                        author_id=odoobot_id,
                        message_type="comment",
                        subtype_xmlid="mail.mt_comment"
                    )
        return None
