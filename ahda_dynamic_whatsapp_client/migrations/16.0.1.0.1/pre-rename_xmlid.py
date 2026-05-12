from odoo.upgrade import util


def migrate(cr, version):
    old_module = "cmp_addition_deletion_revision_approval"
    new_module = "ahda_dynamic_whatsapp_client"

    xmlids = [
        "whatsapp_api_end_point",
        "whatsapp_api_end_point_param_phone",
        "whatsapp_api_end_point_param_message",
        "whatsapp_api_end_point_param_ref",
        "whatsapp_api_end_point_param_scope",
    ]

    for xid in xmlids:
        util.rename_xmlid(
            cr,
            old=f"{old_module}.{xid}",
            new=f"{new_module}.{xid}",
            noupdate=True,
            on_collision="merge",
        )
