# Copyright 2023 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    enable_sale_blanket_order_mis_cash_flow_forecast = fields.Boolean(
        string="Enable MIS Builder Cash Flow Forecast - Sale Blanket Order",
        default=True,
    )
