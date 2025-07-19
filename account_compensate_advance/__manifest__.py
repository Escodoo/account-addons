# Copyright 2024 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Compensate Advance",
    "summary": """
        Account Compensate Advance""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/account-addons",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_journal.xml",
        "views/account_move.xml",
        "wizard/account_compensate_advance_journal.xml",
    ],
}
