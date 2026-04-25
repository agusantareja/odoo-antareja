{
    "name": "Leave|| Approval",
    "version": "13.0.0.0",
    "summary": """
    Leave || Approval
    Refactoring arsitektur approval.
    """,
    "author": "ChatGPT + Agus",
    "depends": ["antareja_approval", "leave"],
    "data": [
        "data/approval_strategy_template_stage_data.xml",
        "views/compensatory_request_views.xml",
        "views/leave_request_views.xml",
    ],
    "installable": True,
    "application": False,
    'pre_init_hook': 'pre_init_hook_function',
    'post_init_hook': 'post_init_hook_function',
}
