# -*- coding: utf-8 -*-
{
    'name': "Purchase - Metalindo",

    'summary': """
        Custom Purchase Addon for Metalindo""",

    'description': """
        Long description of module's purpose
    """,

    'author': "ariehariady@gmail.com",
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
        'mail', 
        'purchase_requisition',
        'purchase',
        'stock',
        'metalindo_vendor',
        'purchase_stock',
        'metalindo_inventory',
        'metalindo_direct_charge',
        # 'metalindo_approval',
    ],

    # always loaded
    'data': [
        #Security
        'security/res_group.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        #Data
        'data/warehouse_cost_center.xml',
        'data/purchase_sequence.xml',
        'data/parameter.xml',
        'data/vendor_code_umkm.xml',
        'data/vendor.code.csv',
        'data/purchase.category.csv',
        'data/recommend_qty_setting.xml',
        'data/mail_template.xml',

        #Report
        'reports/purchase_order_report.xml',
        'reports/bid_tabulation.xml',
        'reports/purchase_order_slip.xml',
        'reports/vendor_acknowledge.xml',
        'reports/purchase_category_detail.xml',

        #Wizard
        'wizard/create_purchase_wizard.xml',
        'wizard/purchase_request_wizard.xml',

        #Views
        'views/purchase_order.xml',
        'views/res_partner_views.xml',
        'views/product_category.xml',
        'views/recommend_qty_setting_views.xml',
        'views/recommended_qty.xml',
        'views/stock_warehouse_orderpoint.xml',
        # 'views/asset_backend.xml',
        'views/res_config_setting.xml',
        # 'views/pie_chart_percent.xml',
        # 'data/pie_chart_percent_data.xml',
        'views/purchase_requisition.xml',
        'views/account_move.xml',
        'views/purchase_request.xml',
        'views/stock_picking.xml',
        'views/kegiatan_umkm.xml',
        'views/purchase_category.xml',
        'views/product_template.xml',
        'views/vendor_code.xml',
        'views/expedite_views.xml',
        'views/menuitem.xml', #<---- letakan menu item selalu dibawah
    ],
}
