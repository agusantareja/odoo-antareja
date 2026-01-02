# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class ApprovalTaskLineMixin(models.AbstractModel):
    _inherit = "approval.task.line.mixin"
    _description = "Approval Task Line Integration Mixin"

    user_delegation_id = fields.Many2one('user.delegation',compute='_compute_user_delegation')

    def _compute_user_delegation(self):
        for rec in self:
            rec.user_delegation_id = rec.get_user_delegation()

    def get_user_delegation(self):
        rec = self.ensure_one()
        delegator_ids = rec.get_users().ids
        return self.env.user.get_delegation(delegator_ids, company_id=rec.company_id)

    def do_approve(self, **kwargs):
        rec = self.ensure_one()
        if kwargs.get('user_delegation') :
            kw = kwargs
        else:
            kw = dict(kwargs)
            kw['user_delegation'] = rec.get_user_delegation()
        return super(ApprovalTaskLineMixin, self).do_approve(**kw)

    def do_reject(self, reason=None, **kwargs):
        rec = self.ensure_one()
        if kwargs.get('user_delegation'):
            kw = kwargs
        else:
            kw = dict(kwargs)
            kw['user_delegation'] = rec.get_user_delegation()
        return super(ApprovalTaskLineMixin,self).do_reject( reason=reason, **kw)


