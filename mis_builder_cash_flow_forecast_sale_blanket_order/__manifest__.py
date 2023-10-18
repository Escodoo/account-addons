# Copyright 2023 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Mis Builder Cash Flow Forecast Sale Blanket Order",
    "summary": """
        MIS Builder Cash Flow Forecast - Sale Blanket Order""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/account-addons",
    "depends": [
        "mis_builder_cash_flow_forecast_integration",
        "sale_blanket_order",
        "queue_job",
    ],
    "data": [
        "views/res_config_settings.xml",
        "views/sale_blanket_order.xml",
        "data/ir_cron.xml",
    ],
}
