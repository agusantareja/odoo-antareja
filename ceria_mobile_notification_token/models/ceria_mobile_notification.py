# -*- coding: utf-8 -*-

import json
from odoo import api, fields, models


class CeriaMobileNotification(models.Model):
    _inherit = "ceria.mobile.notification"

    def event_update_approval(self,data=None):
        super(CeriaMobileNotification,self).event_update_approval(data=data)
        rec = self.ensure_one()
        if rec.notification_type == 'approval' and rec.to_user_id and rec.mobile_approval_id:
            if not data:
                accept_data = json.loads(self.accept_data or "{}")
                data = accept_data.get('data') or {}
            if 'mobile_access_token' in data:
                endpoint = rec.mobile_approval_id.get_endpoint()
                self.env["ceria.mobile.token.user.approval"].create_or_update(
                    request_datetime=rec.mobile_approval_id.request_datetime,
                    user_id=rec.to_user_id,
                    endpoint=endpoint,
                    token=data['mobile_access_token']
                )


