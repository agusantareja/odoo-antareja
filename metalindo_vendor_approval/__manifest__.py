# -*- coding: utf-8 -*-
{
    'name': "Vendor Approval - Metalindo",

    'summary': """
        Vendor Approval Addon for Metalindo""",

    'description': """
        Fitur:
        1. Implementasi alur approval untuk vendor menggunakan modul matrix approval yang ada di modul metalindo_approval.
        2. Menu baru khusus untuk manajemen vendor.
        3. Menu "Vendors" yang ada di modul purchase di-filter agar hanya menampilkan vendor yang approved.
    """,

    'author': "MMS",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Administration',
    'version': '16.0.0.0.0',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'cmp_metalindo_approval',
        'metalindo_vendor',
    ],

    # always loaded
    'data': [
        # Security
        'security/group_users.xml',
        'security/ir.model.access.csv',

        # Data
        'data/mail_template.xml',
       
        # Views
        'views/vendor_approval.xml',
        'views/vendor_blacklist.xml',
        'views/vendors.xml',
    ],

    # Web assets
    'assets': {
        'web.assets_backend': [
            'metalindo_vendor_approval/static/src/css/main.css',
        ],
    },

    # Show as an application
    'application': True,
}
