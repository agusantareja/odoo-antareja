import os
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ApprovalStrategyInlineTemplate(models.AbstractModel):
    _name = "approval.strategy.task.inline.mixin"
    _inherit = ['abstract.approval.type', 'abstract.approval.status', 'approval.transaction.able.mixin','approval.user.task.mixin']
    _description = """
    Inline adalah strategi handel legacy approval task.
    Capture inline untuk keperluan approval view dan management
    """
    sequence = fields.Integer()
    approval_stage_id = fields.Many2one(
        'approval.transaction.stage'
    )

    migrate_to_id = fields.Many2one(
        'approval.transaction.task'
    )

    def prepare_migrate_dict(self):
        return {
            'type_approval': self.type_approval,
            'user_id': self.user_id.id,
            'group_id': self.group_id.id,
            'inline_approval_task_id': self.id,
            'inline_approval_task_model_name': self._name
        }

    def migration_approval_task(self, approval_stage):
        self.ensure_one()
        prepare_dict = self.prepare_migrate_dict()
        prepare_dict['approval_stage_id'] = approval_stage.id
        migrate_to = self.migrate_to_id.create([prepare_dict])[0]
        self.write({
            'migrate_to_id': migrate_to.id,
            'approval_stage_id': approval_stage.id
        })

    def set_transaction_object(self, transaction_object):
        if transaction_object:
            self.write({
                'transaction_id':transaction_object.id,
                'transaction_model_name': transaction_object._name
            })

    def search_for_capture(self,transaction_object,approval_stage):
        return self.search(
            [
                ('status_approval', 'in', ['draft', 'waiting', 'waiting_approval', False]),
                ('transaction_id', '=', transaction_object.id),
                ('transaction_model_name', '=', transaction_object._name),
                ('migrate_to_id', '=', False),
            ]
        )

    def is_link_with_transaction(self):
        return self.get_transaction_object()

    def capture_inline_approval_task_to_stage(self,transaction_object,approval_stage):
        results = self.search_for_capture(transaction_object,approval_stage)
        if results:
            for rec in results:
                rec.migration_approval_task(approval_stage)
            _logger.info(f" Update {rec._name},{rec.id} <== {results.ids}")
        else:
            _logger.warning(f"No Task Data capture from trx {self.transaction_model_name}, {self.transaction_id}")
