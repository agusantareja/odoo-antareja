# -*- coding: utf-8 -*-

from odoo import api, fields, models
import json
import requests
import traceback


class MobileNotificationClient(models.Model):
    _inherit = "mobile.notification.client"

    def prepare_send_data(self,**data):
        data_notif = super().prepare_send_data(**data)
        if self.to_user_id:
            data_notif['mobile_access_token']=self.to_user_id.sudo().get_mobile_access_token(create=True)
        return data_notif
