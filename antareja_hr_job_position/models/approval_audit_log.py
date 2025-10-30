
from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))

class ApprovalAuditLog(models.Model):
    _inherit = 'approval.audit.log'
    employee_id = fields.Many2one(
        'hr.employee',
        "Employee",

    )
    delegator_employee_id = fields.Many2one(
        'hr.employee',
        "Delegator Employee",

    )

    def create_audit_log(self, **kwargs):
        kw = dict(kwargs)
        user_id = kwargs.get('user_id')
        employee_id = kwargs.get('employee_id')
        job_position = kwargs.get('job_position')
        if not user_id:
            user = self.env.user
        else:
            user = self.user_id.browse(user_id)

        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
        else:
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)])
            kw['employee_id'] = employee_id = employee.id

        if not job_position and employee:
           kw['job_position']=job_position = employee.job_id.name or employee.job_title

        delegator_job_position = kwargs.get('delegator_job_position')
        delegator_id = kwargs.get('delegator_id')
        delegator_employee_id = kwargs.get('delegator_employee_id')
        if not delegator_job_position and not delegator_id and delegator_employee_id:
            kw['delegator_job_position']=job_position
            kw['delegator_employee_id'] =employee_id
            kw['delegator_id'] = user.id
        elif delegator_id:
            delegator = self.user_id.browse(delegator_id)
            employee = self.env['hr.employee'].search([('user_id', '=', delegator.id)])
            kw['delegator_employee_id'] = employee.id
            if employee:
                kw['delegator_job_position'] = employee.job_id.name or employee.job_title
        return super(ApprovalAuditLog,self).create_audit_log(**kw)
