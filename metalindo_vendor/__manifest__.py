# -*- coding: utf-8 -*-
{
    'name': "Vendor - Metalindo",

    'summary': """
        Vendor Addon for Metalindo""",

    'description': """
        Fitur:
        1. Vendor code di res.partner.
        2. Filter view "Manufacturer".
        3. Tag "Manufacturer" di res.partner.category untuk menandai partner adalah manufacturer.
    """,

    'author': "Maizar",
    'website': "http://www.metalindo.com",
    'images': [],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Metalindo',
    'version': '1.0',
    'sequence': 5,
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'mail',
        # 'base_address_extended dan zipcode_extende pindah ke
        # 'base_address_extended',
        # 'zipcode_extended',
    ],

    # External dependencies needed by this module
    'external_dependencies': {
        'python': ['phonenumbers']
    },

    # always loaded
    'data': [
        # 'security/group_users.xml',
        'security/ir.model.access.csv',
        # 'data/vendor.code.csv',
        'data/res_partner_category.xml',
        'data/vendor_sequence.xml',
        'views/res_partner.xml',
        'supplier_readonly_view.xml',
        # 'views/vendor_approval.xml',
        # 'views/vendor_blacklist.xml',
        # 'data/res.city.csv',
        # 'data/res.zipcode.csv',
        'data/uppercase_address_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    # res.city.csv and res.zipcode.csv should only be loaded once
    'pre_init_hook': '_load_indonesian_cities_and_zipcodes',
}
