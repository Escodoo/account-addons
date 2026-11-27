# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.model
    def _get_total_for_tax_totals(self):
        """Without a fiscal operation the order total is not rebuilt from the
        fiscal lines, so the stored total cannot be used as the target."""
        order = self.order_id
        if not order.fiscal_operation_id:
            return sum(order.order_line.mapped("price_total"))
        return super()._get_total_for_tax_totals()
