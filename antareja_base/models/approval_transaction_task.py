# -*- coding: utf-8 -*-
from odoo import models, fields, api

import logging

_logger = logging.getLogger(__name__)


class ApprovalTransactionTask(models.AbstractModel):
    _name = "approval.transaction.task.able.mixin"
    _description = """ implement untuk instance yang akan akan di tabahkan approval
    """

    approval_line_for_document = fields.Many2many(
        'approval.audit.log',
        string='Approval Line for Document',
        compute='_compute_approval_line_for_document',
        help="Approval line untuk di pakai di dokument lembar pengesahan"
    )

    def _compute_approval_line_for_document(self):
        for rec in self:
            rec.approval_line_for_document = rec.approval_line_for_document.get_approval_line_for_document(
                self._name,
                rec.id
            )

    def done_approval_transaction_task(self, **kwargs):
        self.unregister_approval_task(**kwargs)

    def unregister_approval_task(self, **kwargs):
        """
        Approval task as done
        """
        self.ensure_one()
        kwargs = dict(kwargs)
        kwargs.update(
            transaction_id=self.id,
            transaction_model_name=self._name,
        )
        self.env['approval.task'].approval_done(**kwargs)
        if kwargs.get("skip_create_approval_log"):
            return
        self.create_approval_log(**kwargs)

    def setup_approval_transaction_task(self, **kwargs):
        return self.register_approval_task(**kwargs)

    def register_approval_task(self, **kwargs):
        return self.register_to_approval_task(**kwargs)

    def get_internal_number(self):
        """
        Default internal description
        """
        if self and hasattr(self, 'name') and self.name:
            return self.name
        return self.display_name

    def get_internal_document(self):
        """
        Default internal document
        """
        if self and hasattr(self, '_description'):
            return self._description
        return None

    def get_internal_description(self):
        """
        Default internal description
        """
        if self and hasattr(self, '_description') and self._description and hasattr(self, 'name') and self.name:
            return f"{self._description} {self.name}"
        return None

    def _find_action_id(self, action_xmlid=None):
        if action_xmlid:
            try:
                return self.env.ref(action_xmlid).id
            except ValueError:
                return None
        else:
            action_id = None
            if hasattr(self, 'get_internal_action_id') and callable(self.get_internal_action_id):
                action = self.get_internal_action_id()
                if isinstance(action, str):
                    try:
                        action_id = self.env.ref(action).id
                    except ValueError:
                        return None
            else:
                action = self.env['ir.actions.act_window'].search([('res_model', '=', self._name)], limit=1)
                if action:
                    action_id = action.id
        return action_id

    def _find_menu_id(self, menu_xmlid=None, action_id=None):
        if menu_xmlid:
            try:
                return self.env.ref(menu_xmlid).id
            except ValueError:
                return None
        else:
            if hasattr(self, 'get_internal_menu_id') and callable(self.get_internal_menu_id):
                menu_id = self.get_internal_menu_id()
                if isinstance(menu_id, str):
                    try:
                        menu_id = self.env.ref(menu_id).id
                    except ValueError:
                        return None
            else:
                menu_id = None
                if action_id:
                    menu = self.env['ir.ui.menu'].search(
                        [('action', '=', f'ir.actions.act_window,{action_id}')],
                        limit=1
                    )
                    if menu:
                        menu_id = menu.id

                # Jika root_menu=True → naik ke menu paling atas
                if menu_id:
                    menu_rec = self.env['ir.ui.menu'].browse(menu_id)
                    while menu_rec.parent_id:
                        menu_rec = menu_rec.parent_id
                    return menu_rec.id

        return menu_id

    def get_internal_url(self, menu_xmlid=None, cids=None, skip_if_no_company=True, action_xmlid=None):
        """
        Generate backend URL untuk record ini.

        :param menu_xmlid: XMLID menu opsional
        :param cids: company IDs opsional
        :param skip_if_no_company: jika True dan company_id kosong, fallback ke env.company.id
        """
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self._find_action_id(action_xmlid)
        menu_id = self._find_menu_id(menu_xmlid, action_id=action_id)
        # Tentukan cids
        if cids is None:
            if 'company_id' in self._fields:
                if self.company_id:
                    cids = self.company_id.id
                elif skip_if_no_company:
                    cids = self.env.company.id
                else:
                    cids = None
            else:
                cids = self.env.company.id

        menu_part = f"&menu_id={menu_id}" if menu_id else ""
        cids_part = f"&cids={cids}" if cids else ""
        action_path = f"&action={action_id}" if action_id else ""
        return f"{base_url}/web#id={self.id}&model={self._name}&view_type=form{menu_part}{cids_part}{action_path}"

    def register_to_approval_task(self, **kwargs):
        """
        Register to approval task system
        """
        self.ensure_one()
        if 'transaction_id' in kwargs:
            kwargs.pop('transaction_id')
        if 'transaction_model_name' in kwargs:
            kwargs.pop('transaction_model_name')
        transaction_id = self.id
        transaction_model_name = self._name

        return self.env['approval.task'].approval_setup(
            transaction_id, transaction_model_name, **kwargs
        )

    def get_approval_transaction_task(self):
        return self.env['approval.task'].search([
            ('transaction_id', '=', self.id),
            ('transaction_model_name', '=', self._name),
        ], limit=1)

    def send_notification_approval(self, **kwargs):
        approval = self.get_approval_transaction_task()
        if approval:
            approval.send_notification(**kwargs)

    def create_approval_log(self, **kwargs):
        self.ensure_one()
        create_d = dict(kwargs)
        create_d['transaction_id'] = self.id
        create_d['transaction_model_name'] = self._name
        return self.env['approval.audit.log'].create_audit_log(**create_d)

    def unlink(self):
        list_ids = self.ids
        model_name = self._name
        result = super(ApprovalTransactionTask, self).unlink()
        self.env['approval.task'].search(
            [('transaction_model_name', '=', model_name), ('transaction_id', 'in', list_ids)]).unlink()
        return result

    @api.model
    def action_reject(self):
        return {
            'name': 'Reject Message',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'popup.reject.message.wizard',
            'target': 'new',
        }

    def reject_from_popup_reject(self,**kwargs):
        raise NotImplemented

    def get_next_approval_task_line(self):
        raise NotImplemented