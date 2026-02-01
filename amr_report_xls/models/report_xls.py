# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).

from io import BytesIO
from odoo import models

import xlwt


class ReportXlsxCompatible(models.AbstractModel):
    _name = 'report.report_xls.abstract'

    def _get_objs_for_report(self, docids, data):
        """
        """
        if docids:
            if isinstance(docids, models.BaseModel):
                return docids
            ids = docids
        elif data and "context" in data:
            ids = data["context"].get("active_ids", [])
        else:
            ids = self.env.context.get("active_ids", [])

        return self.env[self.env.context.get("active_model")].browse(ids)

    def create_xls_report(self, docids, data):
        objs = self._get_objs_for_report(docids, data)
        file_data = BytesIO()
        # workbook = self.get_workbook(file_data)
        workbook = xlwt.Workbook(encoding="UTF-8")
        self.generate_xls_report(workbook, data, objs)
        # workbook.close()
        workbook.save(file_data)
        file_data.seek(0)
        return file_data.read(), "xls"

    def generate_xls_report(self):
        raise NotImplemented
