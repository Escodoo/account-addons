# Copyright 2026 Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale Production Date",
    "summary": """
        Adds a Production Date on Sales Orders and Invoices""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/account-addons",
    "depends": ["sale", "account"],
    "data": [
        "views/sale_order.xml",
        "views/account_move.xml",
    ],
}
