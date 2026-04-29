# -*- coding: utf-8 -*-
{
    'name': "CMP || Material Requisition Approval",
    'summary': "Refactoring approval",
    'description': "Refactoring approval",
    'author': "Agus Muhammad Ramdan",
    'category': 'Accounting',
    'version': '16.0.0.0.2',
    'depends': [
        'base',
        'mail',
        'metalindo_direct_charge',
        'metalindo_approval',
    ],
    # always loaded
    'data': [
        'data/notification_template_approver.xml',
        'data/approval_template_data.xml',

        'views/cni_material_requisition_view.xml',
    ],
}
