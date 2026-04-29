# -*- coding: utf-8 -*-
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = [_name, 'approval.instance.able.mixin']

    # data yang di perlukan oleh approval.task dan mobile.approval.task

    @api.model
    def get_internal_document(self):
        return "Purchase Order"

    @api.model
    def get_internal_description(self):
        return "Purchase Order Approval"

    # untuk build internal url
    @api.model
    def get_internal_menu_id(self):
        return 'purchase.menu_purchase_root'

    # def get_internal_action_id(self):
    #     return 'metalindo_vendor_approval.vendors_action'

    def get_internal_requester_id(self):
        return self.user_id.id

    def get_transaction_value(self):
        if self.state == 'revision' and self.previous_amount > self.amount_total:
            _logger.info("get_transaction_value %s", self.amount_total)
            return 0
        _logger.info("get_transaction_value 0, previous_amount %s > amount_total %s", self.previous_amount, self.amount_total)
        return self.amount_total

    def is_status_waiting_approval(self):
        rec = self.ensure_one()
        approval_instance = rec.approval_instance_id.create_or_get(rec, raise_exception_without_template=False)
        if approval_instance:
            return approval_instance.is_status_waiting_approval()
        else:
            _logger.warning("Approval instance not found for record %s (ID: %s). Fallback to check state.", rec.display_name, rec.id)
            return rec.state == 'waiting_for_approval'

    def create_approval_task_line(self):
        pass

    def validate_request_approval(self):
        pass

    def event_approval_start(self, **kwargs):
        order = self.ensure_one()
        state_reject= order.state
        order.write({
            'state_reject':state_reject,
            'state': 'waiting_for_approval',
            'approval_state': 'rf',
            'flag_reject': False,
        })
        # metalindo_direct_charge  purchase_order.py
        for line in order.order_line:
            line.mr_id.write({
                'mr_status': 'purchased'
            })

    def event_before_approve(self, approval_task_line):
        pass

    def event_approval_done(self, **kwargs):
        # if approval_sts == 0:
        if kwargs.get('is_approved'):
            self.write({
                'state': 'approved',
                'flag_reject': False,
            })
            self.button_confirm()
            for pr in self.order_line.mr_id:
                pr.check_state_done()
            self.env['ir.attachment'].search([
                ('res_id', '=', self.id),
                ('res_model', '=', self._name),
                ('res_field', '=', False),
                '|',
                # Using str() here to prevent a `TypeError` when self.po_report_filename is `False`
                # (i.e., not set). No files should have a name ending with "False", so this should
                # not cause accidental deletion of important attachments.
                ('name', '=like', '%' + str(self.po_report_filename)),
                # Using str() here to prevent a `TypeError` when self.vendor_acknowledge_report_filename
                # is `False` (i.e., not set). No files should have a name ending with "False", so
                # this should not cause accidental deletion of important attachments.
                ('name', '=like', '%' + str(self.vendor_acknowledge_report_filename)),
            ]).unlink()
            self.write({
                'po_report': False,
                'po_report_filename': False,
                'vendor_acknowledge_report': False,
                'vendor_acknowledge_report_filename': False,
                'print_po_date': False,
            })
        elif kwargs.get('is_rejected'):
            self.write({
                'state': self.state_reject or 'draft'
            })
