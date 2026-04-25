# -*- coding: utf-8 -*-

import logging
import jwt

from odoo import models, fields
from jwt import InvalidTokenError, InvalidAudienceError, InvalidIssuerError

_logger = logging.getLogger(__name__)


class AntarejaTokenAudience(models.Model):
    _name = 'antareja.token.audience'
    _description = 'Antareja Token Audience'
    _order = 'name'

    name = fields.Char('Audience', required=True, help='Audience')
    issuer_ids = fields.Many2many('antareja.token.issuer', string='Issuers')

    def get_token_audience(self, audience, issuer):
        _logger.info("audience %s , issuer %s", audience, issuer)
        audience_id = self.sudo().search([('name', '=', audience)], limit=1)
        for issuer_id in audience_id.issuer_ids:
            if issuer_id.name == issuer:
                return audience_id, issuer_id

        for issuer_id in audience_id.issuer_ids:
            if issuer_id.name == "https://" + issuer:
                return audience_id, issuer_id

        return None, None

    def validate(self, token, raise_exception=False):
        try:
            payload = jwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": True,
                    "verify_aud": False,
                    "verify_iss": False,
                }
            )
            audience, issuer = self.get_token_audience(payload.get('aud'), payload.get('iss'))
            if not audience:
                _logger.error(f"Invalid Audience {audience}")
                raise InvalidAudienceError('Invalid Audience')
            if not issuer:
                _logger.error(f"Invalid Issuer {issuer}")
                raise InvalidIssuerError('Invalid Issuer')
            if issuer.validate(token):
                login = payload.get('sub')
                email = payload.get('email')
                user = self.env['res.users'].sudo().search([('login', '=', login)], limit=1)
                if not user:
                    user = self.env['res.users'].sudo().search([('login', '=', login)], limit=1)
                if not user:
                    user = self.env['res.users'].sudo().search([('email', '=', email)], limit=1)
                if not user:
                    user = self.env['res.users'].sudo().search([('partner_id.email', '=', email)], limit=1)
                if user:
                    payload['uid'] = user.id
                    payload['username'] = user.login
                    return payload
                _logger.error(f"User Not found {login} , {email}")
                return payload
        except InvalidTokenError:
            _logger.exception("InvalidTokenError")
            if raise_exception:
                raise

        return None
