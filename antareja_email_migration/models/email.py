from odoo import models, fields, api
from datetime import datetime
import json
import pytz
import requests
import logging
import time

_logger = logging.getLogger(__name__)

class SendEmail(models.Model):
    _inherit = "send_message.email"

    # Refactored send email function
    def send_email(self):
        #jika paramater True maka function ini akan berjalan, jika False maka akan berhenti. setting paramater ini terdapat pada
        #System Paramater
        parameter = self.env['ir.config_parameter'].get_param('send_message_cron.active_send_email_cron')
        if parameter == 'True':
            send = self or self.env['send_message.email'].search([('is_send', '=', False)], limit=10)
            log = self.env['send_message.log']
            now = datetime.now(pytz.timezone('Asia/Jakarta'))
            date_time = now.strftime("%d/%m/%Y %H:%M:%S")
            message = {}
            #looping dahulu data yang ada di tabel
            test_email = self.env['ir.config_parameter'].get_param('send_message_cron.test_email')
            for record in send:
                if not record.template:
                    message["name"] = date_time
                    message["message"] = "Failed no template email"
                    log.create(message)
                    record.write({'is_send': True})
                    self._cr.commit()
                    continue

                template = record.template
                template_values = {
                    'email_from': record.company_id.email,
                    'email_cc': False,
                    'auto_delete': True,
                    'partner_to': False,
                    'scheduled_date': False,
                }
                if test_email != 'False':
                    # testing
                    template_values['email_to']=test_email
                elif record.receiver:
                    # dari receiver user
                    email = record.receiver.partner_id.email
                    if email:
                        template_values['email_to']=email
                else:
                    email_ex = record.email_ex
                    #jika ada email maka akan lanjut
                    if email_ex:
                        template_values['email_to']=email_ex

                if  not template_values.get('email_to',False) :
                    message["name"] = date_time
                    message["message"] = "Failed no email for %s" % (record.receiver.name)
                    record.write({'is_send': True})
                    self._cr.commit()
                    continue
                try:
                    mail_template = template.sudo().send_mail(record.id_record, email_values=template_values)
                    message["name"] = date_time
                    message["message"] = "Success to send email %s" % (mail_template)
                    record.write({'is_send': True})
                    self._cr.commit()
                except Exception:
                    message["name"] = date_time
                    message["message"] = "Something wrong when send email please check log"
                    record.write({'is_send': True})
                    self._cr.commit()
                    self.failed_send_mail_message(record.id, "email")
                    self.failed_send_wa_message("email")
                log.create(message)

    def failed_send_mail_message(self, record_id, type:str):
        template_email = ""
        if type == "email":
            template_email = self.env.ref('send_message_cron.failed_send_mail_template')
        else:
            template_email = self.env.ref('send_message_cron.failed_send_wa_template')
        groups = self.env.ref('send_message_cron.group_failed_notif_receiver')
        record = self.env['send_message.email'].browse(int(record_id))
        log = self.env['send_message.log']
        message = {}
        now = datetime.now(pytz.timezone('Asia/Jakarta'))
        date_time = now.strftime("%d/%m/%Y %H:%M:%S")
        for user in groups.users:
            template_values = {
                'email_from'    : self.env.company.email,
                'email_to'      : user.partner_id.email,
                'email_cc'      : False,
                'auto_delete'   : True,
                'partner_to'    : False,
                'scheduled_date': False,
            }
            mail_template = template_email.sudo().send_mail(record.id_record, email_values=template_values)
            message["name"] = date_time
            message["message"] = "Success to send email %s" % (mail_template)
            log.create(message)
