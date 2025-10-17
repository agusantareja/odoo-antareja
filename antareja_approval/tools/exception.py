# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

_logger = __import__('logging').getLogger(__name__)


class ShowWizardFormError(Exception):
    def __init__(self, action_form=None):
        self.action_form = action_form or {}

    def get_action_form(self):

        return self.action_form
