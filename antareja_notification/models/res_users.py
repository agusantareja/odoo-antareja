# -*- coding: utf-8 -*-

from odoo import fields, models, _
import logging
_logger = logging.getLogger(__name__)


from odoo import models, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    def send_odoobot_message(self, message):
        """Kirim pesan lewat OdooBot ke user ini"""
        #v16
        odoobot = self.env.ref('base.partner_root')
        for user in self:
            try:
                with self.env.cr.savepoint():
                    if self._uid != user.id:
                        self = self.with_user(user)
                    channel_info = self.env['mail.channel'].channel_get([odoobot.id])
                    channel = self.env['mail.channel'].browse(channel_info['id'])
                    channel.message_post(
                        body=_(message),
                        author_id=odoobot.id,
                        message_type='comment',
                        subtype_xmlid='mail.mt_comment',
                    )
                    user.sudo().odoobot_state = 'onboarding_emoji'

            except Exception:
                _logger.info('User #%i %s error chanel.',user.id, user.name)

