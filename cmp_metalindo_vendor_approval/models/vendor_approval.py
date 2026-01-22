from odoo import api, fields, models, _


class ResPartnerVendorApproval(models.Model):
    _name = 'res.partner'
    _inherit = [_name, "cni.approval.transaction.task.able.mixin"]

    def send_email_notif(self, partner, trx):
        pass

    def send_wa_notif(self, partner, trx):
        pass

    def compute_approver_group(self):
        """Compute untuk alert approver"""
        for rec in self:
            approver = rec.get_next_approval_task_line()
            if approver:
                param = self.env['ir.config_parameter'].sudo().get_param('metalindo_approval.alert_waiting_approval')
                approver_name = approver.group_id.display_name
                users_approval_notification = rec.get_users_approval_notification()
                approver_user = " / ".join([user.name for user in users_approval_notification])
                approver_name = approver_name + " ( " + approver_user + " )"
                rec.alert_waiting_approval = param.replace("{approver}", str(approver_name))
            else:
                rec.alert_waiting_approval = ""

    def get_internal_description(self):
        return "Vendor Approval"

    # def register_approval_task(self, **kwargs):
    #     kwargs = dict(kwargs)
    #     if 'description' not in kwargs:
    #         kwargs['description'] = "Vendor Approval"
    #     super(ResPartnerVendorApproval, self).register_approval_task(**kwargs)
    #

    # def register_to_approval_task(self, **kwargs):
    #     kwargs = dict(kwargs)
    #     if 'description' not in kwargs:
    #         kwargs['description'] = "Vendor Approval"
    #     super(ResPartnerVendorApproval, self).register_to_approval_task(**kwargs)

    def button_request_approval(self):
        rec = self.ensure_one()
        rec.action_request_approval()

    def event_approval_start(self,**kwargs):
        self.write({'state': 'waiting', 'flag_reject': False})

    def button_approve_approval(self):
        rec = self.ensure_one()
        rec.action_approve()

    def event_approval_done(self,is_approved=False):
        # if approval_sts == 0:
        if is_approved:
            final_state = 'blacklisted' if self.approval_type == 'blacklist' else 'approved'
            self.sudo().write({
                'state': final_state,
                'approval_type': False,
                'flag_reject': False,
                'change_data': False
            })
            # The vendor documents' states must also be updated accordingly
            if self.document_ids:
                self.document_ids.sudo().write({'state': 'approved'})

        # return approval_sts

    # def _compute_website_readonly(self):
    #     partner_supplier = self.browse()
    #     for record in self.filtered(lambda r: r.supplier_rank > 0 ):
    #         record.website_readonly =  record.state != 'draft'
    #         partner_supplier |= record
    #     other_partner = self - partner_supplier
    #     super(ResPartnerVendorApproval, other_partner)._compute_website_readonly()
    #
    # def _compute_category_id_readonly(self):
    #     partner_supplier = self.browse()
    #     for record in self.filtered(lambda r: r.supplier_rank > 0):
    #         record.category_id_readonly =  record.state != 'draft'
    #         partner_supplier |= record
    #     other_partner = self - partner_supplier
    #     super(ResPartnerVendorApproval, other_partner)._compute_category_id_readonly()
    #
    # def _search_base_res_partner_search_mode(self, operator, value):
    #     res_partner_search_mode = self.env.context.get('res_partner_search_mode')
    #     if 'supplier' == res_partner_search_mode:
    #         return self._search_supplier_select_able(operator, value)
    #     return super()._search_base_res_partner_search_mode( operator, value)
