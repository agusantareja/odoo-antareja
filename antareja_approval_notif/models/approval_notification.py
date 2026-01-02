# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class ApprovalStageNotificationConfig(models.AbstractModel):
    _name = "approval.stage.notification.config"
    _description = """
    Notification config
    """
    # setup when configuration
    mail_bot_template_approval_id = fields.Many2one(
        'mail.template', string='Mail Bot Template Approval',
        help="Email template used for approval notifications.")

    mail_bot_template_rejection_id = fields.Many2one(
        'mail.template', string='Mail Bot Template Rejection',
        help="Email template used for rejection notifications.")

    email_template_approval_id = fields.Many2one(
        'mail.template', string='Email Template Approval',
        help="Email template used for approval notifications.")

    email_template_rejection_id = fields.Many2one(
        'mail.template', string='Email Template Rejection',
        help="Email template used for rejection notifications.")

    whatsapp_template_approval_id = fields.Many2one(
        'mail.template', string='Whatsapp Template Approval',
        help="Email template used for approval notifications.")

    whatsapp_template_rejection_id = fields.Many2one(
        'mail.template', string='Whatsapp Template Rejection',
        help="Email template used for rejection notifications.")
