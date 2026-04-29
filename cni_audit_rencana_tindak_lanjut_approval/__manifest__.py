# -*- coding: utf-8 -*-

{
    'name'          : "CNI Audit Rencana Tindak Lanjut || Approval",
    'description'   : """CNI Audit Rencana Tindak Lanjut || Approval""",
    'category'      : 'Audit',
    'depends'       : ['cni_audit', 'antareja_base',],
    "installable"   : True,
    'data': [
        'views/rencana_tindak_lanjut_views.xml'
    ],
    'post_init_hook': 'post_init_hook',
}
