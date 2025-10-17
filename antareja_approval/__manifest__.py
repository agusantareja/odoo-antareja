{
    'name': 'Antareja || Approval',
    'version': '13.0.0.0.1',
    'summary': """
    Approval Workflow and notification
    """,
    'category': 'Tools',
    'author': 'ChatGPT + Agus',
    'depends': ['base', 'mail','antareja_base', 'antareja_notification'],
    'data': [
        'data/notification_template_data.xml',
        'security/ir.model.access.csv',
        'views/approval_transaction_instance_views.xml',
        'views/approval_transaction_stage_views.xml',
        'views/approval_transaction_task_views.xml',
        'views/approval_audit_log_views.xml',
        'views/approval_strategy_template_instance_views.xml',
        'views/menuitem_views.xml',
        'wizard/popup_reject.xml',
        'wizard/approval_strategy_config_stage_views.xml',
    ],
    'installable': True,
    'application': True,
}
