# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    enable_contract_mis_cash_flow_forecast = fields.Boolean(
        string="Enable MIS Builder Cash Flow Forecast - Contract",
        readonly=False,
        related="company_id.enable_contract_mis_cash_flow_forecast",
    )
    contract_mis_cash_flow_forecast_interval = fields.Integer(
        string="Number of contract forecast Periods",
        related="company_id.contract_mis_cash_flow_forecast_interval",
        readonly=False,
    )
    contract_mis_cash_flow_forecast_rule_type = fields.Selection(
        [("monthly", "Month(s)"), ("yearly", "Year(s)")],
        related="company_id.contract_mis_cash_flow_forecast_rule_type",
        readonly=False,
    )
