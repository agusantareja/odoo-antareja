{
    'name': 'Antareja || Approval Tiered Matrix',
    'version': '13.0.0.0.1',
    'summary': """
    Approval Workflow and notification
    """,
    'category': 'Tools',
    'author': 'ChatGPT + Agus',
    'depends': ['base', 'mail', 'antareja_approval_manager', 'antareja_notification'],
    'data': [
        'security/ir.model.access.csv',
        'views/approval_matrix_tiered_rule_views.xml',
        'views/menuitem_views.xml',

    ],
    'installable': True,
    'application': False,
}
