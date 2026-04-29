# -*- coding: utf-8 -*-

import traceback
import logging
from odoo import models, fields, api, _
from odoo.addons.antareja_base.tools.utils import call_retry

_logger = logging.getLogger(__name__)


class CompensatoryRequest(models.Model):
    _name = "leave.compensatory_request"
    _inherit = [_name,'api.call.retry.able.mixin']

    # def api_call_error_callback(self):
    #     rec = self
    #     if rec.state == 'submitted':
    #         rec.write({
    #             'state': 'approved'
    #         })

    @call_retry()
    def create_compensatory_request(self):
        super(CompensatoryRequest, self).create_compensatory_request()
        # for rec in self:
        #     try:
        #         super(CompensatoryRequest, rec).create_compensatory_request()
        #     except Exception:
        #         rec.need_retry_method('create_compensatory_request', traceback.format_exc())
        #         if rec.state == 'submitted':
        #             rec.write({
        #                 'state': 'approved'
        #             })

    # def update_compensatory_request_approval(self):
    #     context = "approval"
    #     self.update_compensatory_request(context)
    #
    # def update_compensatory_request_compensatory(self):
    #     context = "compensatory"
    #     self.update_compensatory_request(context)

    @call_retry()
    def update_compensatory_request(self,context):
        super(CompensatoryRequest, self).update_compensatory_request(context)
        # for rec in self:
        #     try:
        #         super(CompensatoryRequest, rec).update_compensatory_request(context)
        #
        #     except Exception:
        #         rec.need_retry_method('update_compensatory_request_'+context, traceback.format_exc())
        #         if rec.state == 'submitted':
        #             rec.write({
        #                 'state': 'approved'
        #             })


    # def create_compensatory_request(self):
    #     """untuk create compensatory request di hr lewat API"""
    #     for rec in self:
    #         base_hr = self.env['ir.config_parameter'].get_param('hr.cerindocorp.id')
    #         api = self.env['ir.config_parameter'].get_param('leave.rest_api_create_compensatory_request')
    #         if "http" not in api:
    #             url = base_hr + api
    #         else:
    #             url = api
    #         token = self.env['ir.config_parameter'].get_param('leave.token_hr')
    #         lines = []
    #         company_id = None
    #         request_date = rec.request_date.strftime("%Y-%m-%d")
    #         date_of_join = rec.date_of_join.strftime("%Y-%m-%d") if rec.date_of_join else None
    #         if rec.company_id.id == 1:
    #             company_id = 1
    #         elif rec.company_id.id == 3:
    #             company_id = 3
    #         elif rec.company_id.id == 7:
    #             company_id = 7
    #         elif rec.company_id.id == 8:
    #             company_id = 8
    #         elif rec.company_id.id == 9:
    #             company_id = 9
    #         else:
    #             company_id = 5
    #         for line in rec.line_id:
    #             date = line.date.strftime("%Y-%m-%d")
    #             lines.append({
    #               "attendance_id": line.attendance_id.id,
    #               "date": date,
    #               "day": line.day
    #             })
    #
    #         approvals = []
    #         for approval in rec.leave_cr_approval_id:
    #             approvals.append({
    #                 "employee": approval.user_id.name,
    #                 "job": approval.job_id.name,
    #                 "status": approval.status,
    #                 "api_id": approval.id
    #             })
    #         data = {
    #           "name": rec.name,
    #           "employee_id": rec.employee_id.id,
    #           "department_id": rec.department_id.id if rec.department_id else None,
    #           "date_of_join": date_of_join,
    #           "leave_type_id": rec.leave_type_id.odoo_id,
    #           "line_id": json.dumps(lines),
    #           "request_date": request_date,
    #           "reason": rec.reason,
    #           "approval_ids": json.dumps(approvals),
    #           "company_id": company_id
    #         }
    #
    #         header = {
    #           'token': token
    #         }
    #
    #         request_data = requests.post(url=url, headers=header, data=data)
    #         response = request_data.json()
    #
    #         if response['status'] == "success":
    #             rec.write({
    #               'odoo_id': response['cr_api_id'],
    #               'state': 'approved'
    #             })
    #
    #
    # def update_compensatory_request(self, context):
    #     """untuk update compensatory request di hr"""
    #     for rec in self:
    #         base_hr = self.env['ir.config_parameter'].get_param('hr.cerindocorp.id')
    #         api = self.env['ir.config_parameter'].get_param('leave.rest_api_update_compensatory_request')
    #         if "http" not in api:
    #             url = base_hr + api
    #         else:
    #             url = api
    #         token = self.env['ir.config_parameter'].get_param('leave.token_hr')
    #         lines = []
    #         request_date = rec.request_date.strftime("%Y-%m-%d")
    #         for line in rec.line_id:
    #             date = line.date.strftime("%Y-%m-%d")
    #             lines.append({
    #               "attendance_id": line.attendance_id.id,
    #               "date": date,
    #               "day": line.day
    #             })
    #         approvals = []
    #         for approval in rec.leave_cr_approval_id:
    #             approvals.append({
    #                 "status": approval.status,
    #                 "api_id": approval.id,
    #             })
    #         data = {
    #           "update": context,
    #           "cr_api_id": rec.odoo_id,
    #           "request_date": request_date,
    #           "reason": rec.reason,
    #           "approval_ids": json.dumps(approvals),
    #           "line_id": json.dumps(lines)
    #         }
    #
    #
    #         header = {
    #           "token": token
    #         }
    #         request_data = requests.post(url=url, headers=header, data=data)
    #         response = request_data.json()
    #         if response['status'] == 'success':
    #             if response['state'] == 'approve':
    #                 rec.write({
    #                   'state': 'approved'
    #                 })
    #                 for approval in rec.leave_cr_approval_id:
    #                     if approval.status == 'waiting_approval':
    #                         approval.write({
    #                             'status': 'approved'
    #                             })
    #

