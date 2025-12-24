from odoo import http
from odoo.http import request, Response
import json

from odoo.addons.cni_api.controllers.main import check_valid_token


class SnipeUserController(http.Controller):

    @http.route('/snipeit/users', type='http', auth='public', methods=['GET'], csrf=False)
    @check_valid_token
    def get_snipe_users(self, **kwargs):
        domain = []
        if kwargs.get("employee_num"):
            domain.append(("employee_num", "=", kwargs["employee_num"]))
        if kwargs.get("email"):
            domain.append(("email", "=", kwargs["email"]))

        users = request.env["snipe.user"].sudo().search(domain)
        data = [u.api_output_dict() for u in users]

        return Response(
            json.dumps({"count": len(data), "results": data}, ensure_ascii=False),
            content_type='application/json;charset=utf-8',
            status=200
        )

    @http.route('/snipeit/users/<int:user_id>', type='http', auth='user', methods=['GET'], csrf=False)
    @check_valid_token
    def get_snipe_user_detail(self, user_id, **kwargs):
        """
        GET /api/snipe/users/<id>
        """
        user = request.env["snipe.user"].sudo().browse(user_id)
        if not user.exists():
            return Response(
                json.dumps({"error": "User not found"}, ensure_ascii=False),
                content_type='application/json;charset=utf-8',
                status=404
            )

        data = user.api_output_dict()

        return Response(
            json.dumps(data, ensure_ascii=False),
            content_type='application/json;charset=utf-8',
            status=200
        )
