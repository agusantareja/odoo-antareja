# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import traceback
import logging

from odoo.addons.antareja_base.tools.utils import call_retry

_logger = logging.getLogger(__name__)


class LeaveRequest(models.Model):
    _name = 'leave.leave_request'
    _inherit = [_name, 'api.call.retry.able.mixin']
    def api_call_error_callback(self,**kwargs):
        rec = self
        # if rec.state == 'submitted':
        #     rec.write({
        #         'state': 'approved'
        #     })

    @call_retry()
    def create_leave_request(self):
        super(LeaveRequest, self).create_leave_request()
        # for rec in self:
        #     try:
        #         super(LeaveRequest,rec).create_leave_request()
        #     except Exception:
        #         rec.need_retry_method('create_leave_request', traceback.format_exc())
        #         if rec.state == 'submitted':
        #             rec.write({
        #                 'state': 'approved'
        #             })


    # def update_leave_request_approval(self):
    #     self.update_leave_request("approval")
    #
    # def update_leave_request_leave(self):
    #     self.update_leave_request("leave")

    @call_retry()
    def update_leave_request(self,context):
        super(LeaveRequest, self).update_leave_request(context)
        # for rec in self:
        #     try:
        #         super(LeaveRequest,rec).update_leave_request(context)
        #     except Exception:
        #         rec.need_retry_method('update_leave_request_'+context, traceback.format_exc())
        #         if rec.state == 'submitted':
        #             rec.write({
        #                 'state': 'approved'
        #             })

    @call_retry()
    def update_cancel_revisi(self):
        super(LeaveRequest, self).update_cancel_revisi()
        # for rec in self:
        #     try:
        #         super(LeaveRequest,rec).update_cancel_revisi()
        #     except Exception:
        #         rec.need_retry_method('update_cancel_revisi', traceback.format_exc())
                # if rec.state == 'submitted':
                #     rec.write({
                #         'state': 'approved'
                #     })

    @call_retry()
    def update_lr_from_revisi(self):
        super(LeaveRequest, self).update_lr_from_revisi()
        # for rec in self:
        #     try:
        #         super(LeaveRequest,rec).update_lr_from_revisi()
        #     except Exception:
        #         rec.need_retry_method('update_lr_from_revisi', traceback.format_exc())

    @call_retry()
    def action_dalete_lr_hcis(self):
        super(LeaveRequest, self).update_lr_from_revisi()
        # for rec in self:
        #     try:
        #         super(LeaveRequest,rec).update_lr_from_revisi()
        #     except Exception:
        #         rec.need_retry_method('update_lr_from_revisi', traceback.format_exc())

    @call_retry()
    def set_draft_hcis(self):
        super(LeaveRequest, self).update_lr_from_revisi()
        # for rec in self:
        #     try:
        #         super(LeaveRequest,rec).update_lr_from_revisi()
        #     except Exception:
        #         rec.need_retry_method('set_draft_hcis', traceback.format_exc())

