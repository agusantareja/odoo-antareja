# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

import requests

from odoo import api, fields, models
from odoo.exceptions import AccessDenied, UserError
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.auth_signup.models.res_partner import SignupError, now

import logging
_logger = logging.getLogger(__name__)

from odoo.addons import base
base.models.res_users.USER_PRIVATE_FIELDS.append('oauth_access_token')

class ResUsers(models.Model):
    _inherit = 'res.users'

    oauth_provider_id = fields.Many2one('auth.oauth.provider', string='OAuth Provider')
    oauth_uid = fields.Char(string='OAuth User ID', help="Oauth Provider user_id", copy=False)
    oauth_access_token = fields.Char(string='OAuth Access Token', readonly=True, copy=False)

    _sql_constraints = [
        ('uniq_users_oauth_provider_oauth_uid', 'unique(oauth_provider_id, oauth_uid)', 'OAuth UID must be unique per provider'),
    ]

    @api.model
    def _auth_oauth_rpc(self, endpoint, access_token):
        header = {'Authorization' : f"Bearer {access_token}"}
        param={'access_token': access_token}
        res = requests.get(endpoint, headers = header,params=param )
        return res.json()

    @api.model
    def _auth_oauth_validate(self, provider, access_token):
        """ return the validation data corresponding to the access token """
        oauth_provider = self.env['auth.oauth.provider'].browse(provider)
        validation = self._auth_oauth_rpc(oauth_provider.validation_endpoint, access_token)
        if validation.get("error"):
            raise Exception(validation['error'])
        if oauth_provider.data_endpoint:
            data = self._auth_oauth_rpc(oauth_provider.data_endpoint, access_token)
            validation.update(data)
        return validation

    @api.model
    def _generate_signup_values(self, provider, validation, params):
        oauth_uid = validation['user_id']
        email = validation.get('email', 'provider_%s_user_%s' % (provider, oauth_uid))
        name = validation.get('name', email)
        return {
            'name': name,
            'login': email,
            'email': email,
            'oauth_provider_id': provider,
            'oauth_uid': oauth_uid,
            'oauth_access_token': params['access_token'],
            'active': True,
        }

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """ retrieve and sign in the user corresponding to provider and validated access token
            :param provider: oauth provider id (int)
            :param validation: result of validation of access token (dict)
            :param params: oauth parameters (dict)
            :return: user login (str)
            :raise: AccessDenied if signin failed

            This method can be overridden to add alternative signin methods.
        """
        oauth_uid = validation['user_id']
        try:
            oauth_user = self.search([("oauth_uid", "=", oauth_uid), ('oauth_provider_id', '=', provider)])
            if not oauth_user:
                raise AccessDenied()
            assert len(oauth_user) == 1
            oauth_user.write({'oauth_access_token': params['access_token']})
            return oauth_user.login
        except AccessDenied as access_denied_exception:
            if self.env.context.get('no_user_creation'):
                return None
            state = json.loads(params['state'])
            token = state.get('t')
            values = self._generate_signup_values(provider, validation, params)
            try:
                _, login, _ = self.signup(values, token)
                return login
            except (SignupError, UserError):
                raise access_denied_exception

    @api.model
    def auth_oauth(self, provider, params):
        # Advice by Google (to avoid Confused Deputy Problem)
        # if validation.audience != OUR_CLIENT_ID:
        #   abort()
        # else:
        #   continue with the process
        access_token = params.get('access_token')
        validation = self._auth_oauth_validate(provider, access_token)
        # required check
        if not validation.get('user_id'):
            # Workaround: facebook does not send 'user_id' in Open Graph Api
            if validation.get('id'):
                validation['user_id'] = validation['id']
            else:
                raise AccessDenied()

        # retrieve and sign in user
        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()
        # return user credentials
        return (self.env.cr.dbname, login, access_token)

    def _check_credentials(self, password):
        try:
            return super(ResUsers, self)._check_credentials(password)
        except AccessDenied:
            res = self.sudo().search([('id', '=', self.env.uid), ('oauth_access_token', '=', password)])
            if not res:
                raise

    def _get_session_token_fields(self):
        return super(ResUsers, self)._get_session_token_fields() | {'oauth_access_token'}




    def reset_password(self, login):
        """ retrieve the user corresponding to login (login or email),
            and reset their password
        """
        users = self.search([('login', '=', login)])
        if not users:
            users = self.search([('email', '=', login)])
        if len(users) != 1:
            raise Exception(_('Reset password: invalid username or email'))
        if self.env.context.get('mobile'):
            return users.with_context(mobile=True).action_reset_password()
        else:
            return users.action_reset_password()
    

    def action_reset_password(self):
        """ create signup token for each user, and send their signup url by email """
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else now(days=+1)

        if self.env.context.get('mobile'):
            self.mapped('partner_id').with_context(mobile=True).signup_prepare(signup_type="reset", expiration=expiration)
        else:
            self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)

        # send email to users with their signup url
        template = False
        if create_mode:
            try:
                template = self.env.ref('auth_signup.set_password_email', raise_if_not_found=False)
            except ValueError:
                pass
        if not template:
            template = self.env.ref('auth_signup.reset_password_email')
        assert template._name == 'mail.template'

        template_values = {
            'email_to': '${object.email|safe}',
            'email_cc': False,
            'auto_delete': True,
            'partner_to': False,
            'scheduled_date': False,
        }
        template.write(template_values)

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.") % user.name)
            with self.env.cr.savepoint():
                force_send = not(self.env.context.get('import_file', False))
                template.with_context(lang=user.lang).send_mail(user.id, force_send=force_send, raise_exception=True)
            _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)

    
    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """ retrieve and sign in the user corresponding to provider and validated access token
            :param provider: oauth provider id (int)
            :param validation: result of validation of access token (dict)
            :param params: oauth parameters (dict)
            :return: user login (str)
            :raise: AccessDenied if signin failed

            This method can be overridden to add alternative signin methods.
        """
        oauth_uid = validation['user_id']
        try:
            oauth_user = self.search([("oauth_uid", "=", oauth_uid), ('oauth_provider_id', '=', provider)])
            if not oauth_user:
                raise AccessDenied()
            assert len(oauth_user) == 1
            oauth_user.write({'oauth_access_token': params['access_token']})
            return oauth_user.login
        except AccessDenied as access_denied_exception:
            if self.env.context.get('no_user_creation'):
                return None
            state = json.loads(params['state'])
            token = state.get('t')
            values = self._generate_signup_values(provider, validation, params)
            try:
                _, login, _ = self.signup(values, token)
                return login
            except (SignupError, UserError):
                raise access_denied_exception