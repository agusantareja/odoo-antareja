# -*- coding: utf-8 -*-

import ast
from odoo import api, fields, models


class MobileApproval(models.Model):
    _name = "approval.task.request"
    _order = 'request_datetime,id'

    state = fields.Selection(selection_add=[
        ('accept',),
        ('process', 'Process'),
        ('done', 'Done'),
        ('expired', 'Expired'),
        ('error', 'Error'),
    ])
    request_datetime = fields.Datetime(default=fields.Datetime.now)
    source_application = fields.Char()
    source_model = fields.Char()
    source_res_id = fields.Integer()
    payload = fields.Text()
    errors_message = fields.Char()
    last_error = fields.Datetime()

    def create_request(self, request_type=None, **kwargs):
        if 'unregister_approval' == request_type:
            return self.unregister_approval(kwargs)
        elif 'register_approval' == request_type:
            return self.register_approval(kwargs)
        elif 'unregister_user_approval' == request_type:
            return self.unregister_user_approval(kwargs)

        return self.browse()

    # -------------------------------------------------------
    # PROCESS ACCEPT DATA
    # -------------------------------------------------------
    def get_users_from_client(self, data):
        user_list = data.get('user_list')
        to_users = self.user_id.browse()
        if user_list:
            for user_email in user_list:
                to_users |= self.user_id.search(
                    ['|', ('partner_id.email', '=', user_email), ('login', '=', user_email)], limit=1)
        return to_users

    def unregister_user_approval(self, data):
        if self:
            approval_users = self
        else:
            # request_datetime = data.get('request_datetime')
            # if request_datetime:
            #     request_datetime = fields.Datetime.to_datetime(request_datetime)
            # else:
            #     request_datetime = fields.Datetime.now()
            source_application = data.get('source_application')
            source_model = data.get('source_model')
            source_res_id = int(data.get('source_res_id'))
            domain = [('source_application', '=', source_application), ('source_model', '=', source_model),
                      ('source_res_id', '=', source_res_id)]
            users = self.get_users_from_client(data)
            if users:
                domain.append(('user_id', 'in', users.ids))
            approval_users = self.search(domain)
        approval_users.write({'active': False})

        return approval_users

    def unregister_approval(self, data):
        if self:
            approval_users = self
        else:
            # request_datetime = data.get('request_datetime')
            # if request_datetime:
            #     request_datetime = fields.Datetime.to_datetime(request_datetime)
            # else:
            #     request_datetime = fields.Datetime.now()
            source_application = data.get('source_application')
            source_model = data.get('source_model')
            source_res_id = int(data.get('source_res_id'))
            domain = [('source_application', '=', source_application), ('source_model', '=', source_model),
                      ('source_res_id', '=', source_res_id)]
            users = self.get_users_from_client(data)
            if users:
                domain.append(('user_id', 'in', users.ids))
            approval_users = self.search(domain)
        approval_users.write({'active': False})
        return approval_users

    def register_approval(self, data):
        results = self.browse()
        users = self.get_users_from_client(data)
        for to_user in users:
            results |= self.create_approval_user(
                user_id=to_user.id, **data
            )

        return results

    def create_approval_user(self, **kwargs):
        user_id = kwargs.get('user_id')
        source_application = kwargs.get('source_application')
        source_model = kwargs.get('source_model')
        source_res_id = kwargs.get('source_res_id')
        request_datetime = kwargs.get('request_datetime')
        if request_datetime:
            request_datetime = fields.Datetime.to_datetime(request_datetime)
        else:
            request_datetime = fields.Datetime.now()
        approval_user = self.search([
            ('user_id', '=', user_id),
            ('source_model', '=', source_model),
            ('source_res_id', '=', source_res_id),
            ('source_application', '=', source_application),
        ])
        accept_key = ['source_application', 'source_model', 'source_res_id',
                      'source_number', 'source_document', 'source_originator_name', 'source_url',
                      'source_approval_model', 'source_approval_res_id']
        data = {k: v for k, v in kwargs.items() if k in accept_key}
        data['source_url'] = kwargs.get('source_url') or kwargs.get('url')
        if self.env.context.get('ceria_mobile_local'):
            data['source_local'] = True
        data['request_datetime'] = request_datetime
        if approval_user:
            if request_datetime and approval_user.request_datetime <= request_datetime:
                approval_user.write(data)
            return approval_user
        data.update(
            user_id=user_id
        )
        return self.create(data)

    def api_create_request(self, **data):
        approvals = self.create_request(**data)
        if approvals:
            result = {
                'status': 'success',
                'message': 'Process IDS %s' % approvals.ids,
            }
        else:
            result = {
                'status': 'success',
                'message': 'Data not found',
            }
        return result

    def api_get_approvals(self, user_email=None, offset=0, limit=None, order=None, size=False, **data):

        if isinstance(limit, str):
            limit = int(limit)
        if isinstance(offset, str):
            offset = int(offset)
        domain = []
        if user_email:
            domain.append(('user_id.partner_id.email', '=', user_email))

        source_application = data.get('source_application')
        if source_application:
            domain.append(('source_application', '=', source_application))

        source_model = data.get('source_model')
        if source_model:
            domain.append(('source_model', '=', source_model))
        source_res_id = data.get('source_res_id')
        if source_res_id:
            domain.append(('source_res_id', '=', source_res_id))
        source_number = data.get('source_number')
        if source_number:
            domain.append(('source_number', 'ilike', source_number))

        source_document = data.get('source_document')
        if source_document:
            domain.append(('source_document', 'ilike', source_document))

        source_originator_name = data.get('source_originator_name')
        if source_originator_name:
            domain.append(('source_originator_name', 'ilike', source_originator_name))

        if 'filters' in data:
            domain += ast.literal_eval(data['filters'])

        result = {
            'status': 'success',
            'offset': offset,
            'count': 0,
        }
        if size:
            count = self.search(domain, order=order, count=True)
            result['size'] = count
            if count < 1:
                result.update(
                    message='Data not found',
                    results=[]
                )
                return result

        approvals = self.search(domain, limit=limit, offset=offset, order=order)
        if approvals:
            data_list = [rec.api_output_dict() for rec in approvals]
            result.update(
                count=len(data_list),
                message='Data found',
                results=data_list
            )
        else:
            result.update(
                message='Data not found',
                results=[]
            )

        return result

    def get_mobile_token(self):
        if not self.user_id:
            return None
        return self.user_id.sudo().get_access_token(create=True)

    def get_source_url(self):
        rec = self.ensure_one()
        source_url = rec.source_url
        if source_url and '/web#' in source_url:
            token = rec.get_mobile_token()
            if token:
                source_url = source_url.replace('/web#', "/web_token_access?token_access=%s&" % token)
        return source_url

    def api_output_dict(self):
        rec = self.ensure_one()
        result = {
            'id': rec.id,
            'request_datetime': rec.request_datetime or None,
            'source_application': rec.source_application or None,
            'source_model': rec.source_model or None,
            'source_res_id': rec.source_res_id or None,
            'source_number': rec.source_number or None,
            'source_document': rec.source_document or None,
            'source_originator_name': rec.source_originator_name or None,
            'source_approval_model': rec.source_approval_model or None,
            'source_approval_res_id': rec.source_approval_res_id or None,
            'source_url': rec.get_source_url() or None
        }
        return result

    # def get_endpoint(self):
    #     endpoint =None
    #     if self.source_url and '/web#' in self.source_url:
    #         endpoint = self.source_url.split('/web#')[0]
    #     return endpoint
