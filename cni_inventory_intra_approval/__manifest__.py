{
    "name": "CNI || Inventory Intra || Approval",
    "version": "1.0",
    "summary": """
    CNI || Approval Inventory Intra
    Refactoring arsitektur approval.
    """,
    "author": "ChatGPT + Agus",
    "depends": ["antareja_approval", "cni_inventory_intra"],
    "data": [
        "data/approval_strategy_template_stage_data.xml",
        "views/material_requisition_views.xml",
        "views/material_inventory_request_views.xml",
    ],
    "installable": True,
    "application": False,
    'pre_init_hook': 'pre_init_hook_function',
    'post_init_hook': 'post_init_hook_function',
}
