# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).

from odoo.http import content_disposition, request, route, serialize_exception
from odoo.tools import html_escape
from odoo.tools.safe_eval import safe_eval
from odoo.addons.web.controllers import main as report
import time
import json


class ReportController(report.ReportController):

    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter == "xls":
            return self._report_routes_xls(reportname, docids, converter, **data)
        return super(ReportController, self).report_routes(
            reportname, docids, converter, **data
        )

    def _report_routes_xls(self, reportname, docids=None, converter=None, **data):
        try:
            report = request.env["ir.actions.report"]._get_report_from_name(reportname)
            context = dict(request.env.context)
            if docids:
                docids = [int(i) for i in docids.split(",")]
            if data.get("options"):
                data.update(json.loads(data.pop("options")))
            if data.get("context"):
                # Ignore 'lang' here, because the context in data is the one
                # from the webclient *but* if the user explicitely wants to
                # change the lang, this mechanism overwrites it.
                data["context"] = json.loads(data["context"])
                if data["context"].get("lang"):
                    del data["context"]["lang"]
                context.update(data["context"])
            xls = report.with_context(context).render_xls(docids, data=data)[0]
            report_name = report.report_file
            if report.print_report_name and docids:
                if not len(docids) > 1:
                    obj = request.env[report.model].browse(docids[0])
                    report_name = safe_eval(
                        report.print_report_name,
                        {"object": obj, "time": time, "data": data, "ctx": context}
                    )
                else:
                    obj = request.env[report.model].browse(docids)
                    report_name = safe_eval(
                        report.print_report_name,
                        {"objects": obj, "time": time, "data": data, "ctx": context, 'multi': True}
                    )

            xlshttpheaders = [
                ("Content-Type", "application/vnd.ms-excel",),
                ("Content-Length", len(xls)),
                ("Content-Disposition", content_disposition(report_name + ".xls")),
            ]
            return request.make_response(xls, headers=xlshttpheaders)
        except Exception as e:
            se = serialize_exception(e)
            error = {"code": 200, "message": "Odoo Server Error", "data": se}
            return request.make_response(html_escape(json.dumps(error)))
