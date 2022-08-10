# Copyright 2022 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Mis Builder Cash Flow Forecast Contract",
    "summary": """
        MIS Builder Cash Flow Forecast Contract Integration""",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/account-addons",
    "depends": [
        "mis_builder_cash_flow_forecast_integration",
        "contract",
        "queue_job",
    ],
    "data": [
        "views/res_config_settings.xml",
        "views/res_company.xml",
        "data/contract_forecast_line_cron.xml",
    ],
    "demo": [],
}
