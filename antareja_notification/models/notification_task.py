# -*- coding: utf-8 -*-

from odoo import fields, models, _
import logging

_logger = logging.getLogger(__name__)


class NotificationTaskMixin(models.AbstractModel):
    _name = "notification.task.mixin"
    _description = "Mixin task perlu untuk notif ke user"

    notification_user_ids = fields.Many2many("res.users")
    notification_template_id = fields.Many2one('notification.template')

    def get_notification_object(self):
        return self

    def send_notification(self):
        if self.notification_template_id:
            obj = self.get_notification_object()
            self.notification_template_id.send_notification_to_users(self.notification_user_ids,obj.id)
