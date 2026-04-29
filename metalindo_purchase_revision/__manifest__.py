# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Revision - Metalindo",

    'summary': """
        Purchase Order Revision Addon for Metalindo""",

    'description': """
        Purchase Order Revision Addon for Metalindo
    """,

    'author': "maizarrahman1@gmail.com",
    'website': "http://www.metalindo.com",
    'images': [],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Metalindo',
    'version': '1.0',
    'sequence': 6,
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': [
        'base', 
        'purchase_requisition',
        'purchase',
        'stock',
        'purchase_stock',
        'metalindo_purchase',
        'metalindo_inventory',
        'metalindo_approval',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/group_users.xml',
        'wizard/request_revision.xml',
        'wizard/reject_revision.xml',
        'data/system_parameter.xml',
        'data/mail_template.xml',
        'views/purchase_order.xml',
        'report/report_purchaseorder.xml',
    ],
}
