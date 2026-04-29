# -*- coding: utf-8 -*-

from odoo import models, fields, api
import matplotlib.pyplot as plt, mpld3
import pytz
from datetime import datetime


class PieChartPercent(models.Model):
    _name = 'pie.chart.percent'
    _description = 'pie chart with percentage labels'

    name = fields.Char('Title')
    awal = fields.Date('From')
    akhir = fields.Date('To')
    pie_chart = fields.Text(string='Pie Chart', compute='_compute_pie_chart')
    detil = fields.Html(string='Data', compute='_compute_pie_chart')

    @api.onchange('awal', 'akhir')
    def onchange_awal_akhir(self):
        judul1 = ''
        judul2 = ''
        if self.awal:
            judul1 = 'From ' + self.awal.strftime('%-d %b %Y')
        if self.akhir:
            judul2 = 'To ' + self.akhir.strftime('%-d %b %Y')
        self.name = judul1 + ' ' + judul2

    def _compute_pie_chart(self):
        # import pdb; pdb.set_trace()
        for rec in self:
            # Pie chart data
            query = """SELECT vc.name as label, ROUND(SUM(po.amount_total/po.currency_rate)) as nilai
                    FROM purchase_order po 
                    LEFT JOIN res_partner rp ON po.partner_id = rp.id
                    LEFT JOIN vendor_code vc ON rp.code_id = vc.id 
                    WHERE po.state IN ('purchase', 'done') """
            group_by = " GROUP BY vc.name ORDER BY label "
            # get user's timezone
            user_id = self.env['res.users'].browse(self.env.uid)
            user_tz = pytz.timezone(user_id.partner_id.tz) or pytz.timezone('Asia/Jakarta')
            if rec.awal:
                awal7 = datetime(rec.awal.year, rec.awal.month, rec.awal.day, 0, 0, 0, tzinfo=user_tz)
            if rec.akhir: 
                akhir7 = datetime(rec.akhir.year, rec.akhir.month, rec.akhir.day, 23, 59, 59, tzinfo=user_tz)

            if rec.awal and rec.akhir:
                tgl = " AND po.date_order BETWEEN '" + str(awal7.astimezone(pytz.utc)) + "' AND '" + str(akhir7.astimezone(pytz.utc)) + "' "
            elif rec.awal and not rec.akhir:
                tgl = " AND po.date_order >= '" + str(awal7.astimezone(pytz.utc)) + "' "
            elif not rec.awal and rec.akhir:
                tgl = " AND po.date_order <= '" + str(akhir7.astimezone(pytz.utc)) + "' "
            else:
                tgl = ''

            self.env.cr.execute(query + tgl + group_by)
            data = self.env.cr.dictfetchall()
            total = sum(list(map(lambda x : x['nilai'], data)))
            if total == 0:
                rec.pie_chart = False
                rec.detil = False
                continue
            # labels = ['Frogs', 'Hogs', 'Dogs', 'Logs']
            # sizes = [15, 30, 45, 10]  # in percent
            labels = []
            sizes = []
            lain = 0
            rp_lain = 0
            detil = ''
            for dat in data:
                nilai = round((dat['nilai']/total) * 100.0, 1)
                if nilai >= 1.0 and dat['label']:
                    labels.append(dat['label'])
                    sizes.append(nilai)
                else:
                    lain += nilai
                    rp_lain += dat['nilai']
                label = ''
                if dat['label']:
                    label = dat['label']
                detil += '<tr><td>' + label + '</td><td>Rp ' + f"{int(dat['nilai']):,}".replace(',', '.') + '</td><td>' + str(nilai).replace('.', ',') + '%</td></tr>'
            labels.append('Lain-Lain')
            sizes.append(lain)

            # Irisan ke-2 sedikit terpisah
            # explode = (0, 0.1, 0, 0)
            # ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
            #         shadow=True, startangle=90)

            fig1, ax1 = plt.subplots()
            ax1.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=True, startangle=0)

            # Equal aspect ratio ensures that pie is drawn as a circle
            ax1.axis('equal')
            
            rec.pie_chart = mpld3.fig_to_html(fig1)
            rec.detil = '<table class="table table-bordered"><tbody>' + detil + '</tbody></table>'


