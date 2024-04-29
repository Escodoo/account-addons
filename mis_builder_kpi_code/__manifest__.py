# Copyright 2024 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "MIS Builder KPI Code",
    "summary": """
        MIS Builder KPI Code""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/account-addons",
    "depends": ["mis_builder"],
    "data": [
        "views/mis_report.xml",
        "report/mis_report_instance_qweb.xml",
    ],
    "qweb": [
        "static/src/xml/mis_report_widget.xml",
    ],
    "demo": [],
}
