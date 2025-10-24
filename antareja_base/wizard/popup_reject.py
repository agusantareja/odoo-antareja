from odoo import fields, models
from datetime import datetime

class PopupRejectMessageWizard(models.TransientModel):
    _name = "popup.reject.message.wizard"
    _description = "Popup Reject Message"

    name = fields.Text(string="Note", required=True)
    def get_note_reject(self):
        return "Note Reject => %s"%(self.name)

    def button_reject(self):
        context = self.env.context
        obj = self.env[context.get('active_model')].browse(context.get('active_id'))
        obj.with_context(dict(context, default_notes=self.name,__reject_reason=self.name)).reject_from_popup_reject(
            reason=self.name,
            popup_reject=self
        )
        #message = "Note Reject => %s"%(self.name)

        # mail bot
        # if context.get('mail_bot'):
        #     obj.mail_reject()

        # if context.get('mr'):
        #     obj.write({
        #         'flag_note'       : True,
        #         'notes'           : message+" by "+str(self.env.user.partner_id.name),
        #         'request_status'  : 'draft'
        #         })
        #     for rec in obj.approval_ids:
        #         rec.write({
        #             'approve': False
        #         })
        #
        # if context.get('mir'):
        #     obj.write({
        #         'flag_note'       : True,
        #         'notes'           : message+" by "+str(self.env.user.partner_id.name),
        #         'request_status'  : 'draft'
        #     })
        #
        # if context.get('lr'):
        #     obj.write({
        #         'flag_note'       : True,
        #         'notes'           : message+" by "+str(self.env.user.partner_id.name),
        #         'state'          : 'draft'
        #     })
        #     for rec in obj.leave_approval_ids:
        #         rec.write({
        #             'status': 'waiting_approval'
        #         })
        #
        # if context.get('cr'):
        #     obj.write({
        #         'flag_note'       : True,
        #         'notes'           : message+" by "+str(self.env.user.partner_id.name),
        #         'state'          : 'draft'
        #     })
        #     for rec in obj.leave_cr_approval_id:
        #         rec.write({
        #             'status': 'waiting_approval'
        #         })
        #
        # if context.get('la_waiting'):
        #     obj.write({
        #         'notes' : message+" by "+str(self.env.user.partner_id.name),
        #         'state' : 'draft'
        #     })
        #
        # if context.get('la_verification'):
        #     obj.write({
        #         'notes' : message+" by "+str(self.env.user.partner_id.name),
        #         'state' : 'draft'
        #     })
        #     for rec in obj.approval_id:
        #         rec.write({'status': 'waiting'})
        #
        # if context.get('la_survey_approval'):
        #     obj.write({
        #         'notes' : message+" by "+str(self.env.user.partner_id.name),
        #         'state' : 'verification'
        #     })
        #
        #     for rec in obj.survey_approval_id:
        #         rec.write({'status': 'waiting'})
        #
        # if context.get('la_cost_control'):
        #     obj.write({
        #         'notes' : message+" by "+str(self.env.user.partner_id.name),
        #         'state': 'draft'
        #     })
        #     for rec in obj.approval_id:
        #         rec.write({'status': 'waiting'})
        #
        #     for rec in obj.survey_approval_id:
        #         rec.write({'status': 'waiting'})
        #
        # if context.get('p2h'):
        #     message = "Rejected by %s, reason: %s" %(str(self.env.user.partner_id.name), self.name)
        #     obj.write({
        #         'status': 'rejected'
        #     })
        #
        # if context.get('sk_legal'):
        #     message = "Rejected by %s, reason: %s"%(str(self.env.user.partner_id.name), self.name)
        #     obj.write({
        #         'state': 'draft',
        #         'notes' : message+" by "+str(self.env.user.partner_id.name),
        #         'flag_note'       : True
        #     })
        #
        # if context.get('sk_approval'):
        #     message = "Rejected by %s, reason: %s"%(str(self.env.user.partner_id.name), self.name)
        #     obj.write({
        #         'state': 'draft',
        #         'notes' : message+" by "+str(self.env.user.partner_id.name),
        #         'flag_note'       : True
        #     })

        # if context.get('hse'):
        #     message = "Rejected by %s, reason: %s"%(str(self.env.user.partner_id.name), self.name)
        #     obj.write({
        #         'state': 'draft',
        #         'reject_reason': self.name,
        #     })
        #
        # if context.get('hse_review'):
        #     message = "Rejected by %s, reason: %s"%(str(self.env.user.partner_id.name), self.name)
        #     obj.write({
        #         'state': 'draft',
        #         'reject_reason': self.name,
        #     })

        # self.env['mail.message'].sudo().create({
        #     'model'         : context.get('active_model'),
        #     'res_id'        : context.get('active_id'),
        #     'message_type'  : 'comment',
        #     'author_id'     : self.env.user.partner_id.id,
        #     'date'          : datetime.now(),
        #     'body'          : message,
        # })
