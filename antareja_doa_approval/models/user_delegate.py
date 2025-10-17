# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.addons.antareja_approval.tools.exception import ShowWizardFormError


class UserDelegate(models.Model):
    _name = 'user.delegate'
    _inherit = [
        _name,
        'approval.transaction.mixin'
    ]

    # add state for approval
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_approval', 'Waiting Approval'),
        ('approved', 'Approved'),
    ])
    request_date = fields.Date(
        default=fields.Date.context_today,
    )
    # Konvension name
    # stage_{strategy}_id
    # stage_hr_employee_id = fields.Many2one(
    #     'approval.transaction.stage',
    #     string='Stage',
    #     help="Stage HR Employee configuration for approval process"
    # )

    def get_requester_id(self):
        """ Return the ID of the delegator user. """
        self.ensure_one()
        return self.delegator_id.id

    def action_button_submit(self):
        self.ensure_one()
        try:
            return self.strategy_button_submit()
        except ShowWizardFormError as e:
            return e.get_action_form()

    def get_prepared_state(self):
        return ['approved'] + super(UserDelegate,self).get_prepared_state()
