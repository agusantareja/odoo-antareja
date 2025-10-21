import os

from odoo.addons.antareja_approval.tools.exception import ShowWizardFormError
from odoo import models, fields, api
import requests
import logging

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    approver_id = fields.Many2one(
        'hr.employee',
        string='Approver'
    )


_strategy_config_name = "hr_employee_doa"
_transaction_stage_field = 'stage_' + _strategy_config_name + '_id'


class ApprovalStrategyConfigStage(models.TransientModel):
    _name = "approval.strategy.config.stage." + _strategy_config_name
    _inherit = ["approval.strategy.config.stage"]
    _table = "approval_strategy_config_stage"
    _description = """
    
    Helper for create new Approval Hr Employee Config
    '
    not add prsistent data ini this model, add at `approval.strategy.config.stage` model.
    """

    ########################################################
    def get_max_level_approver(self):
        """Get the maximum level of approver for HR employee."""
        # This method is used to determine the maximum level of approvers
        # for the HR employee approval strategy.
        # It can be customized based on specific business logic.
        return 2  # Default to 2 levels of approvers

    def create_new_stage(self, source=None):
        """Create a new approval stage for HR employee."""
        user_ids = []
        if not source:
            source = {}
        requester_id = source.get("requester_id") or self.env.context.get('default_requester_id')
        employees = self.env["hr.employee"].search([('user_id', '=', requester_id)])
        max_level_approver = source.get(
            'max_level_approver',
            self.get_max_level_approver()
        )
        if len(employees) == 1:
            emp = employees[0]
            while emp.approver_id and len(user_ids) < max_level_approver:
                emp = emp.approver_id
                if emp.user_id:
                    user_ids.append(emp.user_id.id)

        if user_ids:
            source['approval_tasks'] = [(0, 0,{"user_id": user_id,"type_approval": "user"}) for user_id in user_ids]
        else:
            source['approval_tasks'] = \
                [(0, 0,
                  {
                      "group_id": self.env.ref('base.group_erp_manager').id,  # Default to admin user if no approver found
                      "type_approval": "group"
                  }) ]
            #raise self.raise_error(source, message="No approver found for the HR employee.", )

        # Create a new stage
        return super(ApprovalStrategyConfigStage, self).create_new_stage(source)

    # ########################################################
    # rule when stage running

    # def validate_approval_before_approve(self, transaction_object, approval_stage_object):
    #     """
    #     Validate approval stages before approving.
    #     This method should be overridden by child models to provide specific
    #     approval validation logic.
    #     """
    #     # Example validation logic
    #     pass
