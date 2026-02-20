import os

from odoo import models, fields, api
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    approver_id = fields.Many2one(
        'hr.employee',
        string='Approver'
    )

    def get_users_approval_employee(self,requester,company,max_level_approver=2):
        requester_id = requester and int(requester) or self.env.context.get('default_requester_id')
        domain = [('user_id', '=', requester_id)]
        if company:
            domain.append(('company_id','=',company.id))
        employees = self.env["hr.employee"].search(domain)
        user_ids = self.env['res.users'].browse()
        if len(employees) == 1:
            emp = employees[0]
            while emp.approver_id and len(user_ids) < max_level_approver:
                emp = emp.approver_id
                if emp.user_id:
                    user_ids|=emp.user_id
        return user_ids
