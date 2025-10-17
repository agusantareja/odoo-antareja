# -*- coding: utf-8 -*-
from odoo import models, fields, tools, api
from odoo.exceptions import ValidationError


class Approved(models.Model):
    _name = "approval.transaction.approved"
    _auto = False
    _inherit = "abstract.approval.access"
    _description = "Approval Transaction Data Waiting Approval"

    name = fields.Char('Name')
    description = fields.Char()
    request_date = fields.Date()
    requester_id = fields.Many2one(
        'res.users',
        'Requester ID'
    )
    transaction_id = fields.Integer(
        'Transaction ID'
    )
    transaction_model_name = fields.Char(
        'Transaction Model Name'
    )
    approval_stage_id = fields.Integer('Approval Stage ID')
    approval_stage_model_name = fields.Char('Approval Model Name')

    approval_line_id = fields.Integer(
        'Approval Line ID',
        help="ID of the approval line associated with this transaction"
    )
    approval_model_name = fields.Char(
        'Approval Line Model Name'
    )
    user_id = fields.Many2one(
        'res.users',
        string="User",
    )
    # proxy_user_id = fields.Many2one(
    #     'res.users',
    #     string="Acting User"
    # )
    # delegator_user_id = fields.Many2one(
    #     'res.users', string="On Behalf Of"
    # )
    action_type = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('proxy_approve', 'Proxy Approve'),
        ('proxy_reject', 'Proxy Reject'),
    ])
    notes = fields.Text()
    create_date = fields.Datetime(string='Action Time', readonly=True)

    def init(self):
        super(Approved, self).init()
        ConfigUnion = self.env['approval.config.union']
        if not ConfigUnion.view_exists(self._table):
            ConfigUnion.create_view(self._name, self._table, raise_error_if_fail=False)
        if not ConfigUnion.view_exists(self._table):
            """Initialize the model by creating a SQL view."""
            query = """
                with dw as (
                    select
                        stage.name,
                        stage.description,
                        stage.request_date,
                        stage.requester_id,
                        stage.transaction_id,
                        stage.transaction_model_name,
                        stage.approval_task_id ,
                        stage.approval_task_model_name,
                        stage.action_type,
                        stage.user_id ,
                        stage.create_date
                    from approval_audit_log stage 
                    )
                    select row_number() over () as id, * from dw
                """

            tools.drop_view_if_exists(self.env.cr, self._table)
            self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, query))

    def get_transaction_object(self):
        """Get the parent document ID if available."""
        # This method should be overridden in child classes if needed
        return self.env[self.transaction_model_name].browse(self.transaction_id)

    def get_approval_object(self):
        """Get the parent document ID if available."""
        # This method should be overridden in child classes if needed
        return self.env[self.approval_stage_model_name].browse(self.approval_stage_id)

    def action_show_detail(self):
        self.ensure_one()
        obj = self.get_transaction_object()
        if not obj:
            raise ValidationError("Transaction object not found for ID: {}".format(self.transaction_id))
        return {
            'type': 'ir.actions.act_window',
            'name': obj._description,
            'res_model': obj._name,
            'view_mode': 'form',
            'res_id': obj.id,
        }

    def action_my_approval_transaction(self):
        records = self.search_for_current_user()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Approvals',
            'res_model': self._name,
            'view_mode': 'tree,form',
            'domain': [('id', 'in', records.ids)],
            'context': dict(self.env.context),
        }
