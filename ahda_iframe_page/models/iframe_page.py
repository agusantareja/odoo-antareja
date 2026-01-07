# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import html_translate


class iframe_page(models.Model):
    _name = 'iframe.page'
    _description = 'Iframe Page'

    url = fields.Char(string="Iframe URL",required=True)
    active = fields.Boolean(string="Active", default= True)
    name = fields.Char('Menu Title',required=True)
    menu_id = fields.Many2one('ir.ui.menu','Menu')
    parent_menu_id = fields.Many2one('ir.ui.menu','Parent Menu')
    menu_icon = fields.Binary('Menu Icon',attachment=True)
    sequence = fields.Integer('Sequence')
    iframe_txt = fields.Text('Iframe Source')
    iframe_html = fields.Html(compute="_compute_iframe_html",sanitize=False)
    action_id = fields.Many2one('ir.actions.act_window','Action')

    def unlink(self):
        for rec in self:
            rec.menu_id.unlink()
            rec.action_id.unlink()
        return super().unlink()

    @api.depends('url')
    def _compute_iframe_html(self):
        for rec in self:
            rec.iframe_html = ""
            if rec.url:
                rec.iframe_html += f'<iframe src="{rec.url}" width="100%" height="100%" frameborder="0"></iframe>'
            else:
                rec.iframe_html += '<p>No iframe to display</p>'

    @api.constrains('name','sequence','parent_menu_id','active')
    def create_menu(self):
        menu_obj = self.env['ir.ui.menu'].sudo()
        action_obj = self.env['ir.actions.act_window'].sudo()
        view_id = self.env.ref('ahda_iframe_page.iframe_page_show_form')
        for rec in self:
            vals_action = {
                'name' : rec.name,
                'res_model':'iframe.page',
                'view_mode' : 'form',
                'res_id' : rec.id,
                'view_id' : view_id.id,
            }
            if not rec.action_id:
                rec.action_id = action_obj.create(vals_action)
            else:
                rec.action_id.write(vals_action)

            vals_menu = {
                    'name' : rec.name,
                    'parent_id' : rec.parent_menu_id.id,
                    'sequence' : rec.sequence,
                    'action' : 'ir.actions.act_window,%s'%rec.action_id.id,
                    'active' : rec.active,
                }
            if not rec.menu_id:
                rec.menu_id = menu_obj.create(vals_menu)
            else:
                rec.menu_id.write(vals_menu)
            if not rec.parent_menu_id:
                rec.menu_id.web_icon_data = rec.menu_icon
            
