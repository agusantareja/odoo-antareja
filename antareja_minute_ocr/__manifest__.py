{
    'name': 'Antareja || Minute OCR',
    'version': '13.0.1.0.1',
    "category": "Extra Tools",
    "license" : "LGPL-3",
    'author': "Agus Muhammad Ramdan, Antareja Sinergi Sejahtera",
    'description': "Convert Attacment PDF to Text",
    'depends': ['antareja_ocr_attachment','eg_meeting_management'],
    'data': [

        'data/ir_cron.xml',
        'views/minute_meeting_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False
}
