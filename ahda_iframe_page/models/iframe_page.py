# -*- coding: utf-8 -*-

import json
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


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
    page_type = fields.Selection([('single','Single Page'),('slide','Slide Show')],default="single",string="Page Type")
    html_page = fields.Text()
    source = fields.Selection([('url','URL'),('html','HTML')],default="url")
    auto_refresh = fields.Boolean('Auto Refresh')
    auto_refresh_interval = fields.Integer('Auto Refresh Interval')
    slide_show_url_ids = fields.One2many('iframe.url','iframe_page_id','URLs')

    def unlink(self):
        for rec in self:
            if rec.menu_id:
                rec.menu_id.unlink()
            if rec.action_id:
                rec.action_id.unlink()
        return super(iframe_page, self).unlink()

    def compute_iframe_html(self):
        for rec in self:
            html = """
                <style>
                    body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; background-color: #fff; }
                    .iframe-container { width: 100%; height: 100%; border: none; }
                    [class~=o_readonly],.o_form_view,.oe_form_field{height:100%;}
                    [class~=o_cp_controller]{display:none;}
                    .o_action_manager .o_content {margin:0 !important}
                    .o_form_view{padding:0 !important}
                </style>"""
            if rec.source == 'html':
                rec.iframe_html = html+rec.html_page
            else:
                html += """
                    <div id="display_container" class="iframe-container"></div>
                """

                # Prepare data to be passed to JavaScript
                data = {}
                if rec.page_type == 'single':
                    data = {
                        'pageType': 'single',
                        'source': rec.source,
                        'url': rec.url,
                        'htmlPage': rec.html_page,
                        'autoRefresh': rec.auto_refresh,
                        'interval': rec.auto_refresh_interval * 1000 if rec.auto_refresh_interval else 0
                    }
                elif rec.page_type == 'slide':
                    slides = []
                    for slide in rec.slide_show_url_ids:
                        slides.append({
                            'name': slide.name,
                            'source': slide.source,
                            'url': slide.url,
                            'htmlPage': slide.html_page,
                            'duration': slide.auto_refresh_interval * 1000 if slide.auto_refresh_interval else 5000
                        })
                    data = {
                        'pageType': 'slide',
                        'slides': slides
                    }

                # JavaScript logic to handle display, wrapped in an IIFE to prevent redeclaration errors.
                script = f"""
                    <script type="text/javascript">
                        (function() {{
                            const odooData = {json.dumps(data)};
                            const container = document.getElementById('display_container');

                            function displayContent(source, content) {{
                                if (!container) return;
                                if (source === 'url' && content) {{
                                    // Add a cache-busting parameter to the URL to always force a refresh
                                    const cacheBuster = '_t=' + new Date().getTime();
                                    const refreshedUrl = content.includes('?') ? `${{content}}&${{cacheBuster}}` : `${{content}}?${{cacheBuster}}`;
                                    container.innerHTML = `<iframe src="${{refreshedUrl}}" class="iframe-container" frameborder="0"></iframe>`;
                                }} else if (source === 'html' && content) {{
                                    container.innerHTML = content;
                                }} else {{
                                    container.innerHTML = '<p style="text-align:center; padding-top: 20px;">No content to display.</p>';
                                }}
                            }}

                            if (odooData.pageType === 'single') {{
                                const content = odooData.source === 'url' ? odooData.url : odooData.htmlPage;
                                displayContent(odooData.source, content);

                                if (odooData.autoRefresh && odooData.interval > 0) {{
                                    setInterval(() => {{
                                        const iframe = container.querySelector('iframe');
                                        if (iframe) {{
                                            // To refresh a single page, we can just re-set the src
                                            iframe.src = iframe.src;
                                        }}
                                    }}, odooData.interval);
                                }}
                            }} else if (odooData.pageType === 'slide') {{
                                const slides = odooData.slides;
                                if (slides && slides.length > 0) {{
                                    let currentIndex = 0;
                                    function showNextSlide() {{
                                        if (currentIndex >= slides.length) {{
                                            currentIndex = 0; // Loop back to the start
                                        }}
                                        const slide = slides[currentIndex];
                                        const content = slide.source === 'url' ? slide.url : slide.htmlPage;
                                        
                                        // The displayContent function now handles the refresh automatically
                                        displayContent(slide.source, content);
                                        
                                        const duration = slide.duration > 0 ? slide.duration : 5000;
                                        currentIndex++;
                                        setTimeout(showNextSlide, duration);
                                    }}
                                    showNextSlide();
                                }} else {{
                                    container.innerHTML = '<p style="text-align:center; padding-top: 20px;">No slides configured for this slideshow.</p>';
                                }}
                            }}
                        }})();
                    </script>
                """
                rec.iframe_html = html + script

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
                    'action' : f'ir.actions.act_window,{rec.action_id.id}',
                    'active' : rec.active,
                }
            if not rec.menu_id:
                rec.menu_id = menu_obj.create(vals_menu)
            else:
                rec.menu_id.write(vals_menu)
            if not rec.parent_menu_id and rec.menu_icon:
                rec.menu_id.web_icon_data = rec.menu_icon

class iframe_url(models.Model):
    _name = 'iframe.url'
    _description = 'Iframe URL for Slideshow'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Name')
    html_page = fields.Text('HTML Content')
    source = fields.Selection([('url','URL'),('html','HTML')],default="url", required=True)
    auto_refresh_interval = fields.Integer('Duration (Seconds)', default=10)
    url = fields.Char(string="Iframe URL")
    iframe_page_id = fields.Many2one('iframe.page','Page', ondelete='cascade')
