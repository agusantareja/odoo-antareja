from . import models
from . import controllers
from odoo import api, SUPERUSER_ID

def firebase_post_load():
    # Ambil registry & db cursor dari environment Odoo yang sedang running
    from odoo import registry as reg
    import odoo

    dbname = odoo.tools.config['db_name']
    registry = reg(dbname)
    cr = registry.cursor()

    try:
        env = api.Environment(cr, SUPERUSER_ID, {})
        env['firebase.config']._initialize_firebase()
    finally:
        cr.close()
