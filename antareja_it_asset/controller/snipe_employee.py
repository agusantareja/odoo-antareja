from odoo import http
from odoo.http import request, Response
import json

from odoo.addons.cni_api.controllers.main import check_valid_token


class SnipeEmployeeController(http.Controller):


    @http.route('/snipeit/employee/hardware/<string:nip>', type='http', auth='public', methods=['GET'], csrf=False)
    @check_valid_token
    def get_snipe_user_detail(self, nip, **kwargs):
        """
        GET /api/snipe/employee/hardware/<nip>
        """
        employee = request.env["snipe.user"].sudo().search([('employee_num','=',nip)],limit=1)
        if not employee.exists():
            return Response(
                json.dumps({"error": "Employee not found"}, ensure_ascii=False),
                content_type='application/json;charset=utf-8',
                status=404
            )
        data = employee.api_output_hardware_dict()

        return Response(
            json.dumps(data, ensure_ascii=False),
            content_type='application/json;charset=utf-8',
            status=200
        )
