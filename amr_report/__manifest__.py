# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).

{
    'name': "Report Store",
    'summary': """
        Generate Report and Store
        """,
    'description': """
        Generate Report using background process and Store
    """,
    'author': "Agus Muhammad Ramdan",
    "license": "AGPL-3",
    'website': "https://agus.ramdan.tech",
    'category': 'tools',
    'version': '14.0.0.1.0',
    'depends': ['base', 'web', 'mail'],
    # always loaded
    'data': [
        'data/cron.xml',
        'data/mail_template.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/ir_actions_views.xml',
        'views/report_delay_views.xml',
        'views/report_store_views.xml',
        'wizard/report_download_wizard.xml',
    ],
}
