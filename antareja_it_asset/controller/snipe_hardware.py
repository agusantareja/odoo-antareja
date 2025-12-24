from odoo import http
from odoo.http import request, Response
import json

from odoo.addons.cni_api.controllers.main import check_valid_token


class SnipeHardwareController(http.Controller):

    @http.route('/snipeit/hardware', type='http', auth='public', methods=['GET'], csrf=False)
    @check_valid_token
    def get_hardware(self, **kwargs):
        """
        API GET hardware dari Snipe-IT (data hasil sinkronisasi).
        Bisa difilter dengan query param: employee_num, assigned_to_id
        """
        domain = []
        model = request.env['snipe.hardware'].sudo()
        serial = kwargs.get('serial')
        employee_num = kwargs.get('employee_num')
        #assigned_to_id = kwargs.get('assigned_to_id')
        # Filter berdasarkan serial number di Odoo
        if serial:
            domain.append(('serial', '=', str(serial)))

        # Filter berdasarkan employee number di Odoo
        if employee_num:
            domain.append(('employee_id.nip', '=', str(employee_num)))


        kw = {}
        limit = kwargs.get('limit')
        if limit:
            kw['limit']=int(limit)

        offset = kwargs.get('offset')
        if offset:
            kw['offset'] = int(offset)

        # Ambil data dari database
        hardware_records = model.search(domain,**kw)
        if not hardware_records and serial:
            # bila data tidak ditemukakan berdasarkan serial
            # coba lakukan force udpate berdasarkan serial
            # update dari server bila data serial tidak di temukan
            model.sync_from_snipeit_by_serial(serial)
            hardware_records= model.search(domain)
        # Build output pakai fungsi api_output_dict()
        data = [rec.api_output_dict(with_assigned_to=True) for rec in hardware_records]

        return Response(
            json.dumps({"total": len(data) or 0, "rows": data}),
            content_type='application/json',
            status=200
        )
