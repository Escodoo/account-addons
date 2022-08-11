# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    enable_purchase_mis_cash_flow_forecast = fields.Boolean(
        string="Enable MIS Builder Cash Flow Forecast - Purchase",
        readonly=False,
        related="company_id.enable_purchase_mis_cash_flow_forecast",
    )
