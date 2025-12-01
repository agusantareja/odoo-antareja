# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)

def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))

class ApprovalTransactionTask(models.AbstractModel):
    _inherit = "approval.transaction.task.able.mixin"


    def register_to_approval_task(self, **kwargs):

        rec=self.ensure_one()
        kw = dict(kwargs)

        if 'description' not in kw and have_method(rec,'get_internal_description'):
            kw['description'] = rec.get_internal_description()

        return super(ApprovalTransactionTask,self).register_to_approval_task(**kw)

