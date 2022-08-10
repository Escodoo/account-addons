# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    contract_mis_cash_flow_forecast_interval = fields.Integer(
        string="Number of contract forecast Periods", default=12
    )
    contract_mis_cash_flow_forecast_rule_type = fields.Selection(
        [("monthly", "Month(s)"), ("yearly", "Year(s)")], default="monthly"
    )
    enable_contract_mis_cash_flow_forecast = fields.Boolean(
        string="Enable contract on MIS Cash Flow forecast", default=True
    )
