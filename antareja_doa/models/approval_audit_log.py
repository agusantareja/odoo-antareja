from odoo import models, fields


class ApprovalAuditLog(models.Model):
    _inherit = 'approval.audit.log'
    delegatee_user_id = fields.Many2one('res.users', string="Acting User")
    delegator_user_id = fields.Many2one('res.users', string="On Behalf Of")
    user_delegation_id = fields.Many2one('user.delegation', string="Delegate Rule")
