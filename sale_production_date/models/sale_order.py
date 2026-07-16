# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    production_date = fields.Date()

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.production_date:
            invoice_vals["production_date"] = self.production_date
        return invoice_vals
