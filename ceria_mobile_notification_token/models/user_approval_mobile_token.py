# -*- coding: utf-8 -*-

from odoo import api, fields, models
from firebase_admin import messaging

import json
import traceback


class UserApprovalMobileToken(models.Model):
    _name = "ceria.mobile.token.user.approval"
    user_id = fields.Many2one('res.users', string='User', required=True)
    endpoint = fields.Char("Endpoint", required=True)
    token = fields.Char('Access Token', required=True)
    request_datetime = fields.Datetime(required=True)

    def create_or_update(self,request_datetime=None,user_id=None,endpoint=None,token=None):
        user_id = int(user_id)
        mobile_token= self.search([('user_id','=',user_id),('endpoint','=',endpoint)])
        if mobile_token:
            if mobile_token.request_datetime<request_datetime:
                mobile_token.update({
                    'token':token,
                    'request_datetime':request_datetime
                })
        else:
            mobile_token= self.create([{
                'user_id':user_id,
                'endpoint':endpoint,
                'token':token,
                'request_datetime':request_datetime

            }])[0]
        return mobile_token


