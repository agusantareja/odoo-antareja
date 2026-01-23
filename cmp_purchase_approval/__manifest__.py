# -*- coding: utf-8 -*-
{
    'name': "CMP || Purchase Order Approval",
    'summary': """ Refactoring approval """,

    'description': """
        Custom module for account comunity version
    """,

    'author': "Agus Muhammad Ramdan",
    # 'website': "http://www.yourcompany.com",

    'category': 'Accounting',
    'version': '16.0.1.0.0',
    'depends': [
        'base',
        'cmp_metalindo_approval',
        'cmp_purchase'
    ],
    # always loaded
    'data': [
        'data/notification_template_approver.xml',
        'data/approval_template_data.xml'
    ],
    'post_init_hook': 'post_init_hook',
}
