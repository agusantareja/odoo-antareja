# -*- coding: utf-8 -*-

import ast
from odoo import api, fields, models


class CeriaMobileApproval(models.Model):
    _inherit = "ceria.mobile.approval"

    def get_users_from_client(self,data):
        user_ids = data.get('user_ids')
        if user_ids:
            return self.user_id.browse(user_ids)
        return super(CeriaMobileApproval,self).get_users_from_client(data)

