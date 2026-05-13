{
    'name': "Ceria Mobile Notification and Approval",
    'version': '13.0.1.0.1',
    'depends': ['base', 'cni_api', 'antareja_token', 'ceria_mobile', 'firebase_config'],
    'website': "",
    'description': """Ceria Mobile Notification""",
    'data': [
        'data/cron.xml',
    	'security/ir.model.access.csv',
        'views/ceria_mobile_notification_views.xml',
        'views/menuitem.xml',
    ],
}
