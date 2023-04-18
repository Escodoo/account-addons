# Copyright 2022 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Mis Builder Cash Flow Forecast Purchase",
    "summary": """
        MIS Builder Cash Flow Forecast - Purchase""",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/account-addons",
    "depends": [
        "mis_builder_cash_flow_forecast_integration",
        "purchase",
        "queue_job",
    ],
    "data": [
        "views/res_config_settings.xml",
        "views/purchase_order.xml",
        "data/ir_cron.xml",
    ],
    "demo": [],
}
