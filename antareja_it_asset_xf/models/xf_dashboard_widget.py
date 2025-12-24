# -*- coding: utf-8 -*-
from email import header
from re import M
from this import d
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
import logging
from datetime import datetime,timedelta
import pytz
from dateutil.tz import tzlocal
_logger = logging.getLogger(__name__)
import requests
from lxml import etree


class XFDashboardWidget(models.Model):
    _inherit = 'xf.dashboard.widget'

    def get_hello_widget_data(self):
        company_id = self.env.company.id
        employee_obj = self.env['hr.employee'].sudo().search([('user_id','=',self.env.user.id),('company_id','=',company_id)],order='id desc',limit=1)
        if not employee_obj:
            employee_obj = self.env['hr.employee'].sudo().search([('user_id','=',self.env.user.id)],order='id asc',limit=1)
        data = super(XFDashboardWidget,self).get_hello_widget_data()
        if employee_obj:
            hardware_list = self.env["snipe.hardware"].sudo().search([('employee_id','=',employee_obj.id)])
            data['asset_it'] = ", ".join(set(h.category for h in hardware_list))
        else:
            data['asset_it'] = "-"
        return data
