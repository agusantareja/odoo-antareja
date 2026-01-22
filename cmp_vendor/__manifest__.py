# -*- coding: utf-8 -*-
{
    'name': "CMP || Vendor Address Extended",
    'summary': "Vendor Address Extended",
    'description': """
        Custom module for account comunity version
    """,
    'author': "Agus Muhammad Ramdan",
    'category': 'Accounting',
    'version': '16.0.0.0.0',
    'depends': [
        'base',
        'base_address_extended',
        'zipcode_extended',
        'metalindo_vendor',
    ],
    # always loaded
    'data': [
        'views/base_address_extended_res_partner_view.xml',
        'views/zipcode_extended_res_partner_view.xml',

    ],
}
