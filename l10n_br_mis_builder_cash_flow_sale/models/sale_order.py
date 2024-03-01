# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.depends(
        "partner_id",
        "amount_total",
        "amount_financial_total",
        "pricelist_id",
        "currency_id",
        "order_line.invoice_lines",
        "order_line.qty_invoiced",
        "invoice_ids",
    )
    def _compute_forecast_uninvoiced_amount(self):
        if self.company_id.country_id.code == "BR":
            for order in self:
                amount_invoiced = sum(
                    x.amount_financial_total
                    for x in order.invoice_ids.filtered(
                        lambda x: x.state in ["draft", "posted"]
                    )
                )
                forecast_uninvoiced_amount = (
                    order.amount_financial_total - amount_invoiced
                )
                if (
                    forecast_uninvoiced_amount < 0
                    or order.state
                    in [
                        "cancel",
                    ]
                    or order.invoice_status in ["invoiced"]
                ):
                    forecast_uninvoiced_amount = 0
                if order.forecast_uninvoiced_amount != forecast_uninvoiced_amount:
                    order.update(
                        {
                            "forecast_uninvoiced_amount": order.currency_id.round(
                                forecast_uninvoiced_amount
                            )
                        }
                    )
        else:
            super()._compute_forecast_uninvoiced_amount()
