# Copyright 2024 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Account Compensate Advance",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/account-addons",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/account_menuitem.xml",
        "views/account_journal.xml",
        "wizard/account_create_advance_journal.xml",
        "wizard/account_compensate_advance_journal.xml",
    ],
}
