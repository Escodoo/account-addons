# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def _compute_payment_terms(self, date, total_balance, total_amount_currency):
        """Compute the payment terms.
        :param self:                    The current account.move record.
        :param date:                    The date computed by
                                        '_get_payment_terms_computation_date'.
        :param total_balance:           The invoice's total in company's currency.
        :param total_amount_currency:   The invoice's total in invoice's currency.
        :return:                        A list <to_pay_company_currency,
                                        to_pay_invoice_currency, due_date>.
        """
        values = super()._compute_payment_terms(
            date=date,
            total_balance=total_balance,
            total_amount_currency=total_amount_currency,
        )
        if self.invoice_plan_ids:
            values = []
            for invoice_plan in self.invoice_plan_ids:
                if not invoice_plan.invoiced:
                    total_amount_currency = self.amount_total * (
                        invoice_plan.percent / 100
                    )

                    if (
                        self.currency_id
                        and self.company_id
                        and self.currency_id != self.company_id.currency_id
                    ):
                        cur = self.currency_id
                        total_amount_currency = cur.round(self.total_amount_currency)

                    date = invoice_plan.plan_date
                    total_amount_currency = total_amount_currency
                    total_balance = self._compute_amount_uninvoiced_company_currency(
                        total_amount_currency
                    )

                    values.append(
                        [
                            fields.Date.to_string(date),
                            total_balance,
                            total_amount_currency,
                        ]
                    )

        return values

    # @api.model
    # def _get_mis_cash_flow_forecast_update_trigger_fields(self):
    #     fields = super().self._get_mis_cash_flow_forecast_update_trigger_fields()
    #     return fields + ['invoice_plan_ids']
