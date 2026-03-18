from rsa.common import inverse

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime
import xlrd
import requests
import json
import base64
import tempfile
import binascii
import logging

_logger = logging.getLogger(__name__)


class MaterialRequisition(models.Model):
    _name = 'material.requisition'
    _inherit = [_name, 'approval.transaction.mixin', 'mail.template.internal.mixin']

    # Get the menu ID for the material requisition
    def get_internal_menu_id(self):
        return self.env.ref('cni_inventory_intra.root_menu_material_request').id

    def get_requester_id(self):
        """
        Returns the ID of the user who created the material requisition.
        """
        return self.ensure_one().request_by.id

    # stage_cost_control_mr_id = fields.Many2one(
    #     'approval.transaction.stage',
    #     string='Cost Control Stage',
    #     help="Stage for cost control approval",
    # )
    #
    # stage_inline_mr_id = fields.Many2one(
    #     'approval.transaction.stage',
    #     string='Approval Stage',
    #     help="Stage for approval",
    # )

    def set_starting_status_approval(self):
        self.set_transaction_status('cost_control')

    def action_submit(self):
        for rec in self:
            rec.reset_line_approval()
            rec.validate_before_change_state(rec.request_status, 'cost_control')
            rec.strategy_button_submit()

    def reset_line_approval(self):
        """
        Bila pernah di reject perlu di reset
        """
        self.ensure_one()
        if not self.approval_ids or self.approval_ids.filtered(lambda f: f.status_approval == 'rejected'):
            if self.company_id not in  [3, 7, 8] or self.dynamic_approver :
                self.approval_ids.reset_task_approval()
            else:
                self.write({ 'approval_ids': False,})
                self._onchange_request_by_to_add_approval()

    def validate_before_change_state(self, from_state, to_state):
        # Validasi untuk transisi antar state
        if not self.line_ids:
            raise UserError("Product Harus Diisi")
        if not self.approval_ids:
            raise UserError("Approval Harus Diisi")
        for product in self.line_ids:
            if not product.product_id:
                raise UserError("Product Harus Diisi")

        if from_state == 'cost_control':
            for line in self.line_ids:
                if line.company_id.id not in [7, 8] and not line.cost_center:
                    raise UserError("Mohon lengkapi cost code")

    def set_transaction_status(self, state):
        """
        Set the status of the material requisition.
        """
        self.ensure_one().write({'request_status': state})

    def get_transaction_status(self):
        """
        Returns the current status of the material requisition.
        """
        return self.ensure_one().request_status

    def _get_approval_requests(self):
        return {
            'domain': [('access_approval', '=', True), ('request_status', 'in', ['cost_control', 'waiting_approval'])],
            'view_mode': 'tree,form,kanban',
            'res_model': self._name,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'name': _('To Approve'),
            # 'res_id': self.id,
            'target': 'current',
            'context': {
                'create': 0,
                'delete': 0
            }
        }

    def get_acces_button(self):
        for rec in self:
            rec.acces_button = rec.access_approval

    def search_filter_mr(self, operator, operand):
        obj = self.env.ref('cni_inventory_intra.mr_read_only_group')
        if self._uid in [1, 2]:
            return []
        if self.user_has_groups('base.group_erp_manager'):
            return []
        elif self.env.user.id in obj.users.ids:
            return []
        else:
            user = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.user.id)], limit=1)
            department_id = False
            if user.sudo().department_id.category_id.tingkatan > 2:
                department_id = user.sudo().department_id.parent_id
            elif user.sudo().department_id.category_id.tingkatan == 2:
                department_id = user.sudo().department_id
            elif user.sudo().department_id.category_id.tingkatan < 2:
                department_id = user.sudo().department_id
            else:
                department_id = user.sudo().department_id
            ids = self.search([('request_by', '=', self._uid)]).ids
            ids2 = self.env['material.requisition'].search([('access_approval', '=', True)]).ids
            ids3 = self.env['material.requisition'].search([('department_id', '=', department_id.id)]).ids
            assign_mr_dept = self.env['assign.mr.dept'].sudo().search_employee_mr(user)
            ids4 = self.env['material.requisition'].search([('department_id', 'in', assign_mr_dept)]).ids
            assign_mr_dept_2 = self.env['assign.mr.dept'].sudo().search_department_mr(department_id)
            ids5 = self.env['material.requisition'].search([('department_id', 'in', assign_mr_dept_2)]).ids
            followers = self.env['mail.followers'].sudo().search([('res_model', '=', self._name), ('partner_id', '=', self.env.user.partner_id.id)]).mapped('res_id')
            return [('id', 'in', list(set(ids+ids2+ids3+ids4+ids5+followers)))]
