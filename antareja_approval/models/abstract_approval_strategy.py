# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging


class ApprovalStrategyStage(models.AbstractModel):
    _name = "abstract.approval.strategy.config"
    _inherit = 'abstract.approval.stage.notification'
    _description = """

    This field will configurable in template, config wizard and stage

    """
    sequence = fields.Integer(default=20)
    transaction_model_name = fields.Char('Transaction Model Name')
    transaction_stage_field = fields.Char(
        string='Transaction Stage Field',
        help="Field name in the transaction model that links to this approval stage.")

    stage_mandatory = fields.Boolean()
    stage_strategy_name = fields.Char()
    stage_strategy_config_name = fields.Char(
        string='Stage Strategy Config Name',
        help="""
                Name of the configuration for the stage strategy.
                This field is used to identify the specific configuration for this approval stage.
                It should match the name of a record in the approval strategy configuration model.
                """
    )
    stage_strategy_config_model_name = fields.Char(
        string='Stage Strategy Config Model Name',
        help="""
                Model name for the stage strategy configuration.
                This field is used to specify the model that contains the configuration for this approval stage.
                It should point to the model that defines the strategy configuration logic.
                """
    )
    stage_strategy_inline = fields.Boolean(
        string='Stage Strategy Inline',
        help="""
                Indicates if the approval stage is an inline strategy.

                Meaning task manage/generate in transaction. it legacy from approval strategy.
                If true, the approval stage is managed inline within the transaction model.
                stage_strategy_inline_model_name must be set to the model name
                that handles the inline approval logic.
                If false, the approval stage is managed/create using the standard approval.
                """
    )
    stage_strategy_inline_model_name = fields.Char(
        string='Stage Strategy Inline Model Name',
        help="""
                Model name for the inline approval task.
                This field is used when stage_strategy_inline is true.
                It should point to the model that handles the inline approval logic.
                """
    )
    stage_strategy_inline_migrate = fields.Boolean(
        string='Stage Strategy Inline Migrate',
        help="""
            capture data form legacy model and migrate to model approval_task.
            This strategy when you wil create approval task for legacy way but wil run using new
            """
    )
    stage_dynamic_approval = fields.Boolean(
        string='Stage Dynamic Approval',
        help="""
                Indicates if the approval stage allows dynamic approval.
                If true, the approval stage can dynamically adjust tasks its approval tasks based on the transaction context.
                If false, the approval stage has a fixed set of approval tasks.
                """
    )
    # Stage Approval state in transaction
    status_waiting_approval = fields.Char(
        'Transaction Status: Waiting Approval',
        default='waiting_approval',
        help="""
            Status indicating that the transaction document is waiting for approval.
            When the transaction is status equal with 'status_waiting_approval', this stage active running.
            """
    )
    status_approved = fields.Char(
        'Transaction Status: Approved',
        default='approved',
        help="Status indicating that the transaction document is when transaction approved."
    )
    status_reject = fields.Char(
        'Transaction Status: Rejected',
        default='draft',
        help="Status indicating that the transaction document is when transaction rejected."
    )
