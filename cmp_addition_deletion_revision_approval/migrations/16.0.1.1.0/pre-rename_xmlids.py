from odoo.upgrade import util

def migrate(cr, version):
    old_module = "metalindo_approval"
    new_module = "cmp_addition_deletion_revision_approval"

    xmlids = (
        "menu_metalindo_adr_troubleshoot",
        "adr_troubleshoot_action",
        "adr_troubleshoot_form",
        "matrix_approval_addition_deletion_revision",
        "matrix_approval_line_1",
        "matrix_approval_line_2",
        "matrix_approval_line_3",
        "matrix_approval_line_4",
        "matrix_approval_line_5",
        "matrix_approval_line_6",
        "matrix_approval_line_7",
        "matrix_approval_line_8",
        "matrix_approval_line_9",
        "matrix_approval_line_10",
    )

    for xid in xmlids:
        util.rename_xmlid(
            cr,
            old=f"{old_module}.{xid}",
            new=f"{new_module}.{xid}",
            noupdate=True,
            on_collision="merge",
        )
