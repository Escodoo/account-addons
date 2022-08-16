# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    def invoice_validate(self):
        res = super().invoice_validate()
        for invoice in self:
            purchase = invoice.invoice_line_ids.mapped("purchase_line_id.order_id")
            if purchase:
                purchase._generate_mis_cash_flow_forecast_lines()
        return res
