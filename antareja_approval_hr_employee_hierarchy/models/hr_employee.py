import os

from odoo import models, fields, api
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    approver_id = fields.Many2one(
        'hr.employee',
        string='Approver'
    )

    def get_max_level_approver(self):
        return int(self.env['ir.config_parameter'].sudo().get_param(
            'antareja_approval_hr_employee_hierarchy.max_level_approver')) or 2

    def get_users_approval_employee(self, requester, company, max_level_approver=None):
        max_level_approver = max_level_approver or self.get_max_level_approver()
        requester_id = requester and int(requester) or self.env.context.get('default_requester_id')
        domain = [('user_id', '=', requester_id)]
        if company:
            domain.append(('company_id', '=', company.id))
        employees = self.search(domain)
        user_ids = self.env['res.users'].browse()
        if len(employees) == 1:
            emp = employees[0]
            while emp and len(user_ids) < max_level_approver:
                try:
                    emp = emp.approver_id
                    if emp and emp.user_id and emp.user_id.active:
                        user_ids |= emp.user_id
                except Exception:
                    break
        return user_ids
