# -*- coding: utf-8 -*-
{
    'name': "CMP || Material Issue Request Approval",
    'summary': "Material Issue Request Approval for CMP",
    'description': "Material Issue Request Approval for CMP",
    'author': "Agus Muhammad Ramdan",
    'category': 'Accounting',
    'version': '16.0.0.0.2',
    'depends': [
        'base',
        'mail',
        'metalindo_inventory',
        'metalindo_approval',
    ],
    'data': [
        'data/notification_template_approver.xml',
        'data/approval_template_data.xml',

        'views/cni_material_inventory_request_view.xml',
    ],
    #'post_init_hook': 'post_init_hook',
}
