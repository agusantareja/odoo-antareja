{
    'name': 'CMP || ADR Approval',
    'version': '16.0.1.1.0',
    'sequence': 60,
    'license': 'LGPL-3',
    'summary': 'Customize CMP ADR Approval',
    'author': 'Antareja Sinergi Sejahtera & Raka Hidayat',
    'website': '',
    'depends': [
        'ahda_dynamic_whatsapp_client',
        'metalindo_approval',
        'metalindo_inventory',
    ],
    'data': [
        #Data
        'data/matrix_approval.xml',
        'data/whatsapp_api.xml',
        'data/whatsapp_template_addition_deletion_revision.xml',

        #Views
        'views/addition_deletion_revision_views.xml',
        'views/adr_troubleshoot.xml',
    ],
}
