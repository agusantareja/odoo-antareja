# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LandAcquisitionApproval(models.Model):
    _name = "land.acquisition.approval"
    _inherit = [_name, 'abstract.approval.access', 'approval.transaction.view.able.mixin', 'approval.task.line.mixin', ]
    _order = 'id'
    approval_audit_log_id = fields.Many2one('approval.audit.log')

    # implemant untuk 'abstract.approval.access'
    responsible_user_id = fields.Many2one('res.users', related='user_id')

    # implemant untuk approval.transaction.view.able.mixin
    transaction_id = fields.Integer(compute="compute_transaction_model_name", store=True)
    transaction_model_name = fields.Char(compute="compute_transaction_model_name", store=True)

    def get_transaction_object(self):
        return self.la_id or super(LandAcquisitionApproval, self).get_transaction_object()

    @api.depends('la_id')
    def compute_transaction_model_name(self):
        for rec in self:
            rec.transaction_id = rec.la_id.id
            rec.transaction_model_name = rec.la_id._name

    # implemant untuk approval.task.line.mixin
    def set_approved_status(self, **kwargs):
        self.write({
            'status': 'approved'
        })

    # def set_rejected_status(self, **kwargs):
    #     self.write({
    #         'status': 'reject'
    #     })

    def set_waiting_status(self, **kwargs):
        self.write({
            'status': 'waiting'
        })

    def domain_waiting_status(self):
        return [('status', '=', 'waiting')]


    def write(self, vals):
        result = super(LandAcquisitionApproval, self).write(vals)
        if vals.get('status'):
            for rec in self:
                rec.status== 'approved' and rec.create_audit_log()

        return result

    def create_audit_log(self, create_date=None,user_id=None):
        rec = self
        transaction_object = rec.get_transaction_object()
        if transaction_object:
            al = self.create_approval_audit_log_approved(
                transaction_object=transaction_object,
                transaction_id=transaction_object.id,
                transaction_model_name=transaction_object._name,
                user_id=user_id and int(user_id) or rec.user_id.id,
                name='Approval',
                action_type='approve',
                create_date=create_date or fields.Datetime.now(),
            )
            rec.write({'approval_audit_log_id': al.id})
            return al

    # la_id = fields.Many2one('land.acquisition', string='Land Acquisition')
    # user_id = fields.Many2one('res.users', string='Employee')
    # job_id = fields.Many2one('hr.job', string='Job', compute='_compute_job_id')
    # status = fields.Selection([
    #     ('waiting', 'Waiting Approval'),
    #     ('approved', 'Approved')
    # ], string='Status', default='waiting')
    #
    #
    # @api.depends('user_id')
    # def _compute_job_id(self):
    #     for rec in self:
    #         employee = self.env['hr.employee'].sudo().search([('user_id', '=', rec.user_id.id), ('company_id', '=', self.env.company.id)], limit=1)
    #         rec.job_id = employee.job_id.id


class LandAcquisitonSurveyApproval(models.Model):
    _name = "land.acquisition.survey.approval"
    _inherit = [_name, 'abstract.approval.access', 'approval.transaction.view.able.mixin', 'approval.task.line.mixin', ]

    approval_audit_log_id = fields.Many2one('approval.audit.log')

    # implemant untuk 'abstract.approval.access'
    responsible_user_id = fields.Many2one('res.users', related='user_id')

    # implemant untuk approval.transaction.view.able.mixin
    transaction_id = fields.Integer(compute="compute_transaction_model_name", store=True)
    transaction_model_name = fields.Char(compute="compute_transaction_model_name", store=True)

    def get_transaction_object(self):
        return self.la_id or super(LandAcquisitonSurveyApproval, self).get_transaction_object()

    @api.depends('la_id')
    def compute_transaction_model_name(self):
        for rec in self:
            rec.transaction_id = rec.la_id.id
            rec.transaction_model_name = rec.la_id._name

    # implemant untuk approval.task.line.mixin
    def set_approved_status(self, **kwargs):
        self.write({
            'status':'approve'
        })

    def set_rejected_status(self, **kwargs):
        self.write({
            'status': 'reject'
        })

    def set_waiting_status(self, **kwargs):
        self.write({
            'status': 'waiting'
        })

    def domain_waiting_status(self):
        return [('status','=', 'waiting')]


    def write(self, vals):
        result = super(LandAcquisitonSurveyApproval, self).write(vals)
        if vals.get('state'):
            for rec in self:
                rec.status == 'approved' and rec.create_audit_log()

        return result

    def create_audit_log(self, create_date=None, user_id=None):
        rec = self
        transaction_object = rec.get_transaction_object()
        if transaction_object:
            al = self.approval_audit_log_id.create_audit_log(
                transaction_object=transaction_object,
                transaction_id=transaction_object.id,
                transaction_model_name=transaction_object._name,
                user_id=user_id and int(user_id) or rec.user_id.id,
                name='Approval',
                action_type='approve',
                create_date=create_date or fields.Datetime.now(),
            )
            rec.write({'approval_audit_log_id': al.id})
            return al

    # _description = "land Acquisition Survey Approval"
    # _order = "seq asc"
    #
    # la_id = fields.Many2one('land.acquisition', string='land Acquisition')
    # seq = fields.Integer(string='Sequence')
    # user_id = fields.Many2one('res.users', string='Approver')
    # job_id = fields.Many2one('hr.job', string='Job')
    # status = fields.Selection([
    #     ('waiting', 'Waiting Approval'),
    #     ('approved', 'Approved')
    # ], string='Status', default='waiting')
    #
    #
    #
    # @api.onchange('user_id')
    # def _onchange_user_id(self):
    #     employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.user_id.id)])
    #     if employee:
    #         self.job_id = employee.job_id.id

