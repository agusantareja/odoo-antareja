# -*- coding: utf-8 -*-
from odoo import models, fields, api


class UserDelegate(models.Model):

    _inherit = 'user.delegate'

    notification_option = fields.Selection(
        [('send_to_proxy_only', 'Send to proxy only'),
         ('send_to_both', 'Send to both delegator and proxy')],
        default='send_to_both'
    )

    def get_notification_user_ids(self, user_ids, company_id=None):
        delegations = self.get_all_delegations_for_proxy(company_id=company_id, user_ids=user_ids)
        result = []
        exclude_user_delegate = []
        for delegation in delegations:
            result.append(delegation.proxy_id.id)
            if delegation.notification_option == 'send_to_proxy_only':
                exclude_user_delegate.append(delegation.delegator_id.id)
            else:
                result.append(delegation.delegator_id.id)
        result.extend(set(user_ids)-set(exclude_user_delegate))
        return list(set(result))

    def api_output_delegate_dict(self):
        self.ensure_one()
        result = super().api_output_delegate_dict() or {}
        result['notification_option'] = self.notification_option
        return result
