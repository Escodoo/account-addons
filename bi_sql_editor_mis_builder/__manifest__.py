# Copyright 2025 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "BI SQL Editor MIS Builder",
    "summary": """
        Integrate BI SQL Editor to MIS Builder""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/account-addons",
    "depends": ["bi_sql_editor", "mis_builder"],
    "data": [
        "views/bi_sql_mis_builder_line.xml",
        "views/bi_sql_view.xml",
        "views/mis_report.xml",
        "security/ir.model.access.csv",
        "data/bi_sql_mis_builder_line_cron.xml",
    ],
    "demo": [],
}
