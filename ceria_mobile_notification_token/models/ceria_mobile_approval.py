# -*- coding: utf-8 -*-


from odoo import models


class CeriaMobileApproval(models.Model):
    _inherit = "ceria.mobile.approval"

    def get_source_url(self):
        rec = self.ensure_one()
        source_url = rec.source_url
        if source_url and '/web#' in source_url:
            token = rec.get_mobile_token()
            if token:
                source_url = source_url.replace('/web#', "/web_token_access?token_access=%s&" % token)
        return source_url

    def get_endpoint(self):
        endpoint =None
        if self.source_url and '/web#' in self.source_url:
            endpoint = self.source_url.split('/web#')[0]
        return endpoint

    def get_mobile_token(self):
        if not self.user_id:
            return None
        return self.user_id.sudo().get_access_token(create=True)


