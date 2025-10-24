# -*- coding: utf-8 -*-

from odoo import models, api, fields


class ir_action_server(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(selection_add=[
        ('whatsapp', 'Send WhatsApp Message')],
        ondelete={'whatsapp': 'cascade'},
        help="Type of server action. The following values are available:\n"
             "- 'Update a Record': update the values of a record\n"
             "- 'Create Activity': create an activity (Discuss)\n"
             "- 'Send Email': post a message, a note or send an email (Discuss)\n"
             "- 'Send SMS': send SMS, log them on documents (SMS)"
             "- 'Add/Remove Followers': add or remove followers to a record (Discuss)\n"
             "- 'Create Record': create a new record with new values\n"
             "- 'Execute Code': a block of Python code that will be executed\n"
             "- 'Send Webhook Notification': send a POST request to an external system, also known as a Webhook\n"
             "- 'Execute Existing Actions': define an action that triggers several other server actions\n"
             "- 'Send WhatsApp Message': send a WhatsApp message using the selected template")

    whatsapp_template_id = fields.Many2one('whatsapp.template','WhatsApp Template',domain="[('model_id','=',model_id)]",
        help="WhatsApp template to use for sending WhatsApp messages.")
    
    @api.onchange('model_id')
    def _onchange_model_id(self):
        for action in self:
            action.whatsapp_template_id = False

    def run_action_whatsapp(self, *args, **kwargs):
        for action in self:
            action.whatsapp_template_id.send(kwargs.get('eval_context',{}).get('records'))
        return None
