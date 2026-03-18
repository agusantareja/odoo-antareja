import random
import werkzeug.urls

from collections import defaultdict
from datetime import datetime, timedelta

from odoo import api, exceptions, fields, models, _

class SignupError(Exception):
    pass

def random_token():
    # the token has an entropy of about 120 bits (6 bits/char * 20 chars)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.SystemRandom().choice(chars) for _ in range(20))

def now(**kwargs):
    return datetime.now() + timedelta(**kwargs)

class ResPartner(models.Model):
    _inherit = 'res.partner'


    def _get_signup_url_for_action(self, url=None, action=None, view_type=None, menu_id=None, res_id=None, model=None):
        """ generate a signup url for the given partner ids and action, possibly overriding
            the url state components (menu_id, id, view_type) """

        res = dict.fromkeys(self.ids, False)
        for partner in self:
            base_url = partner.get_base_url()
            # when required, make sure the partner has a valid signup token
            if self.env.context.get('signup_valid') and not partner.user_ids:
                partner.sudo().signup_prepare()

            route = 'login'
            # the parameters to encode for the query
            query = dict(db=self.env.cr.dbname)
            signup_type = self.env.context.get('signup_force_type_in_url', partner.sudo().signup_type or '')
            if signup_type:
                route = 'reset_password' if signup_type == 'reset' else signup_type

            if partner.sudo().signup_token and signup_type:
                query['token'] = partner.sudo().signup_token
            elif partner.user_ids:
                query['login'] = partner.user_ids[0].login
            else:
                continue        # no signup token, no user, thus no signup url!

            if self.env.context.get('mobile'):
                query['mobile'] = self.env.context.get('mobile')

            if url:
                query['redirect'] = url
            else:
                fragment = dict()
                base = '/web#'
                if action == '/mail/view':
                    base = '/mail/view?'
                elif action:
                    fragment['action'] = action
                if view_type:
                    fragment['view_type'] = view_type
                if menu_id:
                    fragment['menu_id'] = menu_id
                if model:
                    fragment['model'] = model
                if res_id:
                    fragment['res_id'] = res_id

                if fragment:
                    query['redirect'] = base + werkzeug.urls.url_encode(fragment)

            url = "/web/%s?%s" % (route, werkzeug.urls.url_encode(query))
            if not self.env.context.get('relative_url'):
                url = werkzeug.urls.url_join(base_url, url)
            res[partner.id] = url

        return res


    def signup_prepare(self, signup_type="signup", expiration=False):
        """ generate a new token for the partners with the given validity, if necessary
            :param expiration: the expiration datetime of the token (string, optional)
        """
        for partner in self:
            if expiration or not partner.signup_valid:
                token = random_token()
                while self._signup_retrieve_partner(token):
                    token = random_token()
                partner.write({'signup_token': token, 'signup_type': signup_type, 'signup_expiration': expiration})
        return True