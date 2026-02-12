# Copyright 2024 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "MIS Builder Custom Reports",
    "summary": """
        MIS Builder Custom Reports""",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/account-addons",
    "depends": ["mis_builder", "web", "l10n_br_base"],
    "assets": {
        "web.assets_backend": [
            "mis_builder_custom_reports/static/src/css/custom.css",
        ],
        "web.report_assets_common": [
            "mis_builder_custom_reports/static/src/css/report.css",
        ],
    },
    "maintainers": ["WesleyOliveira98"],
    "data": [
        "views/mis_report.xml",
        "views/mis_report_instance.xml",
        "report/mis_report_instance_qweb.xml",
    ],
    "demo": [],
}
