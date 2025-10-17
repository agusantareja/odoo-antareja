from odoo import fields, models
from datetime import datetime


class PopupRejectMessageWizard(models.TransientModel):
    _name = "approval.popup.reject.message"
    _description = "Approval Popup Reject message"

    name = fields.Text(string="Note", required=True)

    def button_reject(self):
        context = self.env.context
        obj = self.env[context.get('active_model')].browse(context.get('active_id'))
        # message = "Note Reject => %s"%(self.name)
        # # mail bot
        # if context.get('mail_bot'):
        #     obj.mail_reject()
        #
        obj.with_context(dict(context, __reject_reason=self.name)).callback_reject_from_popup_reject(reject_reason=self.name)

        # self.env['mail.message'].sudo().create({
        #     'model'         : context.get('active_model'),
        #     'res_id'        : context.get('active_id'),
        #     'message_type'  : 'comment',
        #     'author_id'     : self.env.user.partner_id.id,
        #     'date'          : datetime.now(),
        #     'body'          : message,
        # })
