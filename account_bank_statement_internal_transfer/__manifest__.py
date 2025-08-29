# Copyright 2025 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Bank Statement Internal Transfer",
    "summary": """
        Create Internal Transfers from Bank Statements""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/account-addons",
    "depends": ["account_statement_base"],
    "data": [
        "views/account_bank_statement_views.xml",
        "wizard/internal_transfer_wizard.xml",
        "security/ir.model.access.csv",
    ],
}
