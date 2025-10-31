from odoo import fields, models, _
import logging
_logger = logging.getLogger(__name__)


from odoo import models, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    def send_odoobot_message(self, message):
        """Kirim pesan lewat OdooBot ke user ini"""
        self.ensure_one()
        if self._uid != self.id:
            self = self.with_user(self)
        partner = self.partner_id
        odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
        MailChannel = self.env['mail.channel']
        channel = MailChannel.sudo().search([
            ('channel_partner_ids', '=', partner.id),
            ('public', '=', 'private'),
            ('channel_type', '=', 'chat'),
            ('email_send', '=', False),
            ('name', '=', 'OdooBot'),
        ], limit=1)
        if not channel:
            channel = MailChannel.with_context(mail_create_nosubscribe=True).sudo().create({
                'channel_partner_ids': [(4, partner.id)],
                'public': 'private',
                'channel_type': 'chat',
                'email_send': False,
                'name': 'OdooBot'
            })
            self._cr.execute("delete from mail_channel_partner where partner_id = %s and channel_id = %s",
                             [self.env.user.partner_id.id, channel.id])
        result = channel.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment",
                                             subtype="mail.mt_comment")
        self.env.user.odoobot_state = 'onboarding_emoji'
        return result
