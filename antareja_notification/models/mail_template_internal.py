# -*- coding: utf-8 -*-

from odoo import models,fields,api


class InternalUrlMixin(models.AbstractModel):
    _name = 'mail.template.internal.mixin'
    _description = 'Internal URL Mixin (Backend Only with Auto Menu)'

    notification_to_user_id = fields.Many2one(
        'res.users', string='Notification to User',
        compute="_compute_notification_to_user_id",
        help="User who will receive the notification.",
    )

    @api.depends_context('notification_to_user')
    def _compute_notification_to_user_id(self):
        for rec in self:
            rec.notification_to_user_id = self.env.context.get('notification_to_user', False)

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
                action= self.env['ir.actions.act_window'].search([('res_model', '=', self._name)], limit=1 )
                if action:
                    action_id = action.id
        return action_id

    def _find_menu_id(self, menu_xmlid=None,action_id=None):
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
        menu_id = self._find_menu_id(menu_xmlid,action_id=action_id)
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
