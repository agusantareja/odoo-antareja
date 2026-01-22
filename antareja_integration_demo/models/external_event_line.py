import json

from odoo import models, fields


class ExternalEventLine(models.Model):
    _name = 'external.event.line'
    _description = 'External Event Line (JSON-RPC Demo)'

    name = fields.Char(
        string='Name',
        required=True
    )
    auth_id = fields.Many2one(
        'application.server.auth'
    )

    external_app_name = fields.Char(
        string='External App Name'
    )

    external_model = fields.Char(
        string='External Model'
    )

    external_odoo_id = fields.Integer(
        string='External Odoo ID'
    )

    payload = fields.Text()

    def save_payload(self, payload):
        self.payload = json.dumps(payload)

    def action_clear(self):
        self.payload = ""

    def action_search_1(self):
        # xml client
        import xmlrpc.client
        url = self.auth_id.application_server_id.get_endpoint_url()
        db = self.auth_id.get_db_name()
        username, password = self.auth_id.get_username_password()

        # uid untuk helper mengetahui user name
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})
        # xml client
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        ids = models.execute_kw(db, uid, password, "res.partner", "search", [[["is_company", "=", True]]], {"limit": 3})
        self.save_payload(ids)

    def action_search_2(self):
        # cara 2
        ids = self.auth_id.jsonrpc_call('res.partner', 'search', [[("is_company", "=", True)]], {"limit": 5})
        self.save_payload(ids)

    def action_search_3(self):
        # cara 3
        remote_res_partner = self.auth_id.remote_model_object('res.partner')
        ids = remote_res_partner.search([("is_company", "=", True)], limit=10)
        self.save_payload(ids)

    def action_read_1(self):
        # xml client
        import xmlrpc.client
        url = self.auth_id.application_server_id.get_endpoint_url()
        db = self.auth_id.get_db_name()
        username, password = self.auth_id.get_username_password()

        # uid untuk helper mengetahui user name
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})
        # xml client
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        ids = models.execute_kw(db, uid, password, "res.partner", "read", [[3, 4, 5, 68]],
                                {'fields': ['name', 'is_company']})
        self.save_payload(ids)

    def action_read_2(self):
        # cara 2
        ids = self.auth_id.jsonrpc_call('res.partner', 'read', [[3, 4, 5, 6, 7, 69]],
                                        {'fields': ['name', 'is_company']})
        self.save_payload(ids)

    def action_read_3(self):
        # cara 3
        remote_res_partner = self.auth_id.remote_model_object('res.partner')
        ids = remote_res_partner.read([3, 4, 5, 6, 7, 8, 9, 70], fields=['name', 'is_company'])
        self.save_payload(ids)

    def action_search_read_1(self):
        # xml client
        import xmlrpc.client
        url = self.auth_id.application_server_id.get_endpoint_url()
        db = self.auth_id.get_db_name()
        username, password = self.auth_id.get_username_password()

        # uid untuk helper mengetahui user name
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})
        # xml client
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        ids = models.execute_kw(db, uid, password, "res.partner", "search_read",
                                [[("is_company", "=", True)]],
                                {'fields': ['name', 'is_company'], "limit": 5})
        self.save_payload(ids)

    def action_search_read_2(self):
        # cara 2
        ids = self.auth_id.jsonrpc_call('res.partner', 'search_read',
                                        [[("is_company", "=", True)]],
                                        {'fields': ['name', 'is_company'], "limit": 7})
        self.save_payload(ids)

    def action_search_read_3(self):
        # cara 3
        remote_res_partner = self.auth_id.remote_model_object('res.partner')
        ids = remote_res_partner.search_read([("is_company", "=", True)], fields=['name', 'is_company'], limit=10)
        self.save_payload(ids)

    def action_create_1(self):
        # xml client
        import xmlrpc.client
        url = self.auth_id.application_server_id.get_endpoint_url()
        db = self.auth_id.get_db_name()
        username, password = self.auth_id.get_username_password()

        # uid untuk helper mengetahui user name
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})
        # xml client
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        ids = models.execute_kw(db, uid, password, "res.partner", "create",
                                [[{
                                    'name': "test-1"
                                }]])
        self.save_payload(ids)

    def action_create_2(self):
        # cara 2
        ids = self.auth_id.jsonrpc_call('res.partner', 'create',
                                        [[{
                                            'name': "test-2"
                                        }]])
        self.save_payload(ids)

    def action_create_3(self):
        # cara 3
        remote_res_partner = self.auth_id.remote_model_object('res.partner')
        ids = remote_res_partner.create([{'name': "test-3"}])
        self.save_payload(ids)

    def action_write_1(self):
        # xml client
        import xmlrpc.client
        url = self.auth_id.application_server_id.get_endpoint_url()
        db = self.auth_id.get_db_name()
        username, password = self.auth_id.get_username_password()

        # uid untuk helper mengetahui user name
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        uid = common.authenticate(db, username, password, {})
        # xml client
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        ids = models.execute_kw(db, uid, password, "res.partner", "write", [[68], {'name': "test-1-2"}])
        self.save_payload(ids)

    def action_write_2(self):
        # cara 2
        ids = self.auth_id.jsonrpc_call('res.partner', "write", [[69], {'name': "test-2-2"}])
        self.save_payload(ids)

    def action_write_3(self):
        # cara 3
        remote_res_partner = self.auth_id.remote_model_object('res.partner')
        ids = remote_res_partner.write([70], {'name': "test-3-33"})
        self.save_payload(ids)
