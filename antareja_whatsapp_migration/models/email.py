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

    #function ini untuk send wa cron job
    def create_new_wa_message(self, phone:str,message:str,ref:str,id_record=None,model_record=None,partner=None):
        return self.env["notification.template"].create_new_wa_message(
            phone,message,ref,id_record,model_record,partner=partner
        )
    # function ini untuk send wa cron job simplyfiled code
    def send_wa(self):
        parameter = self.env['ir.config_parameter'].get_param('send_message_cron.active_send_wa_cron')
        if parameter == 'True':
            # kirim 1 atau 10 data
            data = self or self.search([('is_send_wa', '=', False)], limit=10)
            test_wa = self.env['ir.config_parameter'].get_param('notif_wa_test')
            for record in data:
                if test_wa != 'False':
                    mobile = test_wa
                else:
                    no_wa = self.env['hr.employee'].search([('user_id', '=', record.receiver.id)], limit=1)
                    if no_wa and no_wa.mobile_phone:
                        mobile = no_wa.mobile_phone
                    else:
                        mobile = record.contact_ex or record.receiver.partner_id.mobile
                if mobile:
                    record.create_new_wa_message(
                        test_wa, record.message, record.ref, id_record=record.id_record,
                        model_record=record.model_record,partner=record.receiver.partner_id
                    )
                record.write({'is_send_wa': True})
                self._cr.commit()

    def failed_send_wa_message(self, type:str):
        groups = self.env.ref('send_message_cron.group_failed_notif_receiver')
        if type == "email":
            param =  self.env["ir.config_parameter"].sudo().get_param("send_message_cron.message_failed_email")
        else:
            param =  self.env["ir.config_parameter"].sudo().get_param("send_message_cron.message_failed_wa")
        for user in groups.users:
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)])
            message_wa = param.replace("{name}", user.partner_id.name)
            if employee and employee.mobile_phone:
                self.create_new_wa_message(employee.mobile_phone, message_wa, "Failed Send Message",partner= user.partner_id)
            else:
                self.create_new_wa_message(user.partner_id.mobile, message_wa, "Failed Send Message", partner=user.partner_id)
