

from odoo import models, fields, api, _


class RencanaTindakLanjutApproval(models.Model):
    _name  = "rencana.tindak.lanjut.approval"
    _inherit = [_name,'abstract.approval.access','approval.transaction.view.able.mixin','approval.task.line.mixin',]

    approval_audit_log_id = fields.Many2one('approval.audit.log')

    # implemant untuk 'abstract.approval.access'
    user_id = fields.Many2one('res.users',related='employee_id.user_id')
    responsible_user_id = fields.Many2one('res.users', related='employee_id.user_id')

    # implemant untuk approval.transaction.view.able.mixin
    transaction_id = fields.Integer(compute="compute_transaction_model_name", store=True)
    transaction_model_name = fields.Char(compute="compute_transaction_model_name", store=True)

    def get_transaction_object(self):
        return self.tindak_lanjut_id or super(RencanaTindakLanjutApproval, self).get_transaction_object()

    @api.depends('tindak_lanjut_id')
    def compute_transaction_model_name(self):
        for rec in self:
            rec.transaction_id = rec.tindak_lanjut_id.id
            rec.transaction_model_name = rec.tindak_lanjut_id._name

    # implemant untuk approval.task.line.mixin
    def set_approved_status(self, **kwargs):
        self.write({
            'state':'approve'
        })

    def set_rejected_status(self, **kwargs):
        self.write({
            'state': 'reject'
        })

    def set_waiting_status(self, **kwargs):
        self.write({
            'state': 'waiting'
        })

    def domain_waiting_status(self):
        return [('state','=', 'waiting')]

    def write(self, vals):
        result = super(RencanaTindakLanjutApproval, self).write(vals)
        if vals.get('status'):
            for rec in self:
                rec.status in ['approved','rejected'] and rec.create_audit_log()

        return result

    def create_audit_log(self, create_date=None):
        rec = self
        transaction_object = rec.cr_id
        if transaction_object:
            if rec.status == 'approved':
                al = rec.create_approval_audit_log_approved(
                    transaction_object=transaction_object,
                    transaction_id=transaction_object.id,
                    transaction_model_name=transaction_object._name,
                    user_id=rec.user_id.id,
                    name='Approval',
                    create_date=create_date or fields.Datetime.now(),
                )
            elif rec.status == 'rejected':
                al = rec.create_approval_audit_log_rejected(
                    transaction_object=transaction_object,
                    transaction_id=transaction_object.id,
                    transaction_model_name=transaction_object._name,
                    user_id=rec.user_id.id,
                    name='Reject',
                    create_date=create_date or fields.Datetime.now(),
                )
            else:
                return None
            rec.write({'approval_audit_log_id': al.id})
            return al

    # _order = "sequence"
    #
    # employee_id = fields.Many2one('hr.employee', string='Employee')
    # state = fields.Selection([
    #     ('waiting', 'Waiting Approve'),
    #     ('approve', 'Approve'),
    #     ('reject', 'Reject')
    # ], string='State', default='waiting')
    # sequence = fields.Integer(string='Sequence')
    # email = fields.Char(string='Email')
    # tindak_lanjut_id = fields.Many2one('rencana.tindak.lanjut', string='Tindak Lanjut')