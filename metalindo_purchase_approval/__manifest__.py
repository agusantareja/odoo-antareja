# -*- coding: utf-8 -*-
{
    'name': "CMP || Purchase Order Approval",
    'summary': """Refactoring approval for purchase order""",

    'description': """
        Custom module for account comunity version
    """,

    'author': "Agus Muhammad Ramdan",
    # 'website': "http://www.yourcompany.com",

    'category': 'Accounting',
    'version': '16.0.0.0.2',
    'depends': [
        'base',
        'mail',
        'purchase',
        'metalindo_purchase',
        'metalindo_purchase_revision',
        'metalindo_inventory',
        'metalindo_approval',
    ],
    # always loaded
    'data': [
        'data/notification_template_approver.xml',
        'data/approval_template_data.xml',

        #'views/cni_purchase_order_view.xml',
    ],
}
