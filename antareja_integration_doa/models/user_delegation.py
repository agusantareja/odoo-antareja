# -*- coding: utf-8 -*-

from odoo import models
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class UserDelegation(models.Model):
    _inherit = 'user.delegation'


    def internal_process_for_doa(self, data_external=None, sync_strategy=None,
                                      data_update=None, data_sync=None, **kwargs):
        delegator = self.lookup_user_external_data(data_external.get('delegator_id'))
        delegatee = self.lookup_user_external_data(data_external.get('delegatee_id'))
        data_update = data_update or {}
        if delegator:
            data_update['delegator_id'] = delegator.id
        else:
            raise ValidationError("Delegator user not found in external data.")

        if delegatee:
            data_update['delegatee_id'] = delegatee.id
        else:
            raise ValidationError("Delegatee user not found in external data.")
        return data_update

    def lookup_user_external_data(self, item_dict):
        if item_dict.get('id') in [1, 2]:
            return self.env['res.users'].browse(item_dict.get('id'))
        return self.env['res.users'].search([('partner_id.email', '=', item_dict.get('email'))], limit=1)
