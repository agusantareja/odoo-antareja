# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MaterialIssueRequest(models.Model):
    _name = 'material.inventory.request'
    _inherit = [_name, 'approval.instance.able.mixin']

    currency_id = fields.Many2one('res.currency', related='company_currency_id')

    # data yang di perlukan oleh approval.instance, approval.task dan mobile.approval.task
    def get_internal_number(self):
        return self.name

    @api.model
    def get_internal_document(self):
        return self._description

    @api.model
    def get_internal_description(self):
        return "Material Issue Request Approval"

    # untuk build internal url
    @api.model
    def get_internal_menu_id(self):
        return 'metalindo_inventory.menu_metalindo_material_inventory_request'

    def get_internal_requester_id(self):
        return self.request_by.user_id.id

    def get_transaction_value(self):
        return self.total_value

    def is_status_waiting_approval(self):
        rec = self.ensure_one()
        approval_instance = rec.approval_instance_id.create_or_get(rec, raise_exception_without_template=False)
        if approval_instance:
            return approval_instance.is_status_waiting_approval()
        else:
            _logger.warning("Approval instance not found for record %s (ID: %s). Fallback to check request_status.", rec.display_name, rec.id)
            return rec.request_status in ['intercompany_approval', 'waiting']

    def create_approval_task_line(self):
        pass

    def validate_request_approval(self):
        pass

    def event_approval_start(self, **kwargs):
        if self.is_intercompany:
            request_status = 'intercompany_approval'
        else:
            request_status = 'waiting'
        self.write({
            'state_reject': request_status,
            'request_status': request_status,
            #'approval_state': 'rf',
            'flag_reject': False,
        })

    def event_before_approve(self, approval_task_line):
        pass

    def event_approval_done(self, **kwargs):
        # if approval_sts == 0:
        if kwargs.get('is_approved'):
            self.write({
                'approved_by': self.approved_by or self.env.uid,
                'approved_date': self.approved_date or fields.Date.context_today(self),
                'completed_by': None,
                'completed_date': None,
                'picked_by': None,
                'picked_date': None,
                'request_status': 'approved'
            })
            self._approve()  # mungkin nanti diganti _picking()
        elif kwargs.get('is_rejected'):
            self.write({
                'request_status':  'draft'
            })

