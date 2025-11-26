from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError, ValidationError
import logging

_logger = logging.getLogger(__name__)


def have_method(obj, method):
    return hasattr(obj, method) and callable(getattr(obj, method))


class ApprovalInstanceAbleMixin(models.AbstractModel):
    _name = 'approval.instance.able.mixin'
    _inherit = [_name, "mail.template.internal.mixin"]

