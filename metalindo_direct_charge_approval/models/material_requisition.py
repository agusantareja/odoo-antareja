# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class MaterialRequisition(models.Model):
    _name = 'material.requisition'
    _inherit = [_name, 'approval.instance.able.mixin']

    def get_internal_number(self):
        return self.name

    @api.model
    def get_internal_document(self):
        return self._description

    @api.model
    def get_internal_description(self):
        return "Material Requisition Approval"

    # untuk build internal url
    @api.model
    def get_internal_menu_id(self):
        return 'metalindo_direct_charge.material_requisition_root_menu'

    @api.model
    def get_internal_action_id(self):
        return 'metalindo_direct_charge.metalindo_material_requisition_action'

    def get_internal_requester_id(self):
        return self.originator_id.id

    def get_transaction_value(self):
        return self.total_cost

    def is_status_waiting_approval(self):
        rec = self.ensure_one()
        approval_instance = rec.approval_instance_id.create_or_get(rec, raise_exception_without_template=False)
        if approval_instance:
            return approval_instance.is_status_waiting_approval()
        else:
            _logger.warning("Approval instance not found for record %s (ID: %s). Fallback to check mr_status.", rec.display_name, rec.id)
            return rec.mr_status == 'waiting'

    def create_approval_task_line(self):
        pass

    def validate_request_approval(self):
        if len(self.line_ids) == 0:
            raise ValidationError(_("Dokumen ini tidak bisa disetujui karena Material belum diisi."))
        for line in self.line_ids:
            if line.product_id.detailed_type == 'service':
                if line.product_id.pr_product_type_id.description != 'SERVICE':
                    raise UserError('''Product Type must be set to "SERVICE"''')
            else:
                if line.product_id.pr_product_type_id.description == 'SERVICE':
                    raise UserError('''You can't choose "SERVICE" as Product Type if PO Type is "Goods"''')

            if not line.priority:
                raise ValidationError(_("Priority tidak boleh kosong !"))
            if line.priority == 'P1' and not line.reason:
                raise ValidationError('Priority (P1), Reason tidak boleh kosong !')

            line.check_product_type_image()

    def event_approval_start(self, **kwargs):
        self.write({
            'mr_status': 'waiting',
            #'approval_state': 'rf',
            'flag_reject': False,
        })

    def event_before_approve(self, approval_task_line):
        group_cost_control = self.env.ref('metalindo_approval.group_finance_cost_control')
        if group_cost_control in approval_task_line.get_groups():
            _logger.info("validation button_approve_cost_control ")
            self.button_approve_cost_control()

    def event_approval_done(self, **kwargs):
        # if approval_sts == 0:
        if kwargs.get('is_approved'):
            self.write({
                'approved_by': self.approved_by or self.env.uid,
                'approved_date': self.approved_date or fields.Date.context_today(self),
                'done_by': None,
                'done_date': None,
                'mr_status': 'approved'
            })
            self.env['input.hs_code'].create({}).with_context(active_ids=[self.id]).action_done()
            self.check_state_done()
        elif kwargs.get('is_rejected'):
            self.write({
                'mr_status': 'draft'
            })
