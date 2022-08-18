# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    def invoice_validate(self):
        res = super().invoice_validate()
        for invoice in self:
            order = invoice.invoice_line_ids.mapped("purchase_line_id.order_id")
            if order and order.company_id.enable_purchase_mis_cash_flow_forecast:
                order.with_delay()._generate_mis_cash_flow_forecast_lines()
        return res
