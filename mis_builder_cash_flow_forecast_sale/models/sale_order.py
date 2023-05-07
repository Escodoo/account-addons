# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    forecast_uninvoiced_amount = fields.Monetary(
        readonly=True,
        compute="_compute_forecast_uninvoiced_amount",
        store=True,
    )

    mis_cash_flow_forecast_line_ids = fields.One2many(
        comodel_name="mis.cash_flow.forecast_line",
        compute="_compute_mis_cash_flow_forecast_line_ids",
        string="Forecast Line",
        required=False,
    )

    mis_cash_flow_forecast_line_count = fields.Integer(
        compute="_compute_mis_cash_flow_forecast_line_ids",
        string="Forecast Line Count",
    )

    @api.depends(
        "partner_id",
        "amount_total",
        "pricelist_id",
        "currency_id",
        "order_line.invoice_lines",
        "order_line.qty_invoiced",
        "invoice_ids",
    )
    def _compute_forecast_uninvoiced_amount(self):
        for order in self:
            amount_invoiced = sum(
                x.amount_total
                for x in order.invoice_ids.filtered(
                    lambda x: x.state in ["draft", "posted"]
                )
            )
            forecast_uninvoiced_amount = order.amount_total - amount_invoiced
            if forecast_uninvoiced_amount < 0 or order.state in [
                "cancel",
            ]:
                forecast_uninvoiced_amount = 0
            if order.forecast_uninvoiced_amount != forecast_uninvoiced_amount:
                order.update(
                    {
                        "forecast_uninvoiced_amount": order.currency_id.round(
                            forecast_uninvoiced_amount
                        )
                    }
                )

    def _compute_mis_cash_flow_forecast_line_ids(self):
        ForecastLine = self.env["mis.cash_flow.forecast_line"]
        forecast_lines = ForecastLine.search(
            [
                ("res_model", "=", self._name),
                ("res_id", "in", self.ids),
            ]
        )

        result = dict.fromkeys(self.ids, ForecastLine)
        for forecast in forecast_lines:
            result[forecast.res_id] |= forecast

        for rec in self:
            rec.mis_cash_flow_forecast_line_ids = result[rec.id]
            rec.mis_cash_flow_forecast_line_count = len(
                rec.mis_cash_flow_forecast_line_ids
            )

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
        if self.payment_term_id:
            to_compute = self.payment_term_id.compute(
                total_balance, date_ref=date, currency=self.company_id.currency_id
            )
            if self.currency_id == self.company_id.currency_id:
                # Single-currency.
                return [(b[0], b[1], b[1]) for b in to_compute]
            else:
                # Multi-currencies.
                to_compute_currency = self.payment_term_id.compute(
                    total_amount_currency, date_ref=date, currency=self.currency_id
                )
                return [
                    (b[0], b[1], ac[1])
                    for b, ac in zip(to_compute, to_compute_currency)
                ]
        else:
            return [(fields.Date.to_string(date), total_balance, total_amount_currency)]

    def _compute_amount_uninvoiced_company_currency(self, amount_uninvoiced):
        if (
            self.currency_id
            and self.company_id
            and self.currency_id != self.company_id.currency_id
        ):
            cur = self.currency_id
            price_subtotal = cur.round(amount_uninvoiced)
            rate_date = self.expected_date or fields.Date.today()
            amount_uninvoiced = cur._convert(
                price_subtotal,
                self.company_id.currency_id,
                self.company_id,
                rate_date,
            )
        return amount_uninvoiced

    @api.model
    def _get_mis_cash_flow_forecast_update_trigger_fields(self):
        return [
            "partner_id",
            "pricelist_id",
            "fiscal_position_id",
            "currency_id",
            "order_line",
            "payment_term_id",
            "currency_rate",
            "invoice_status",
            "state",
            "invoice_ids",
            "invoice_count",
        ]

    def write(self, values):
        res = super(SaleOrder, self).write(values)
        if any(
            [
                field in values
                for field in self._get_mis_cash_flow_forecast_update_trigger_fields()
            ]
        ):
            for rec in self:
                if (
                    values.get("state") in ["sale", "done", "cancel"]
                    or rec.state in ["sale", "done"]
                    and rec.company_id.enable_sale_mis_cash_flow_forecast
                ):
                    rec.with_delay()._generate_mis_cash_flow_forecast_lines()
        return res

    def unlink(self):
        for rec in self:
            if rec.mis_cash_flow_forecast_line_ids:
                rec.mis_cash_flow_forecast_line_ids.unlink()
        return super().unlink()

    def _prepare_mis_cash_flow_forecast_line(
        self, payment_term_item, payment_term_count, date, amount
    ):
        self.ensure_one()
        parent_res_id = self
        parent_res_model_id = self.env["ir.model"]._get(parent_res_id._name)

        # partner = self.partner_id.with_context(force_company=self.company_id.id)
        #
        # account_id = partner.property_account_receivable_id or self.env[
        #     "ir.property"
        # ].get("property_account_receivable_id", "res.partner")

        account_id = (
            self.partner_id.property_account_receivable_id.id
            or self.env["ir.property"]
            ._get("property_account_receivable_id", "res.partner")
            .id
        )

        return {
            "name": "%s - %s/%s"
            % (
                self.display_name,
                payment_term_item,
                payment_term_count,
            ),
            "date": date,
            "account_id": account_id,
            "partner_id": self.partner_id.id,
            "balance": amount,
            "company_id": self.company_id.id,
            "res_model_id": self.env["ir.model"]._get(self._name).id,
            "res_id": self.id,
            "parent_res_model_id": parent_res_model_id.id,
            "parent_res_id": parent_res_id.id,
        }

    def _generate_mis_cash_flow_forecast_lines(self):
        values = []
        for rec in self:
            rec.mis_cash_flow_forecast_line_ids.unlink()
            if rec.forecast_uninvoiced_amount and rec.state in ["sale", "done"]:
                sign = 1
                amount_uninvoiced = rec.forecast_uninvoiced_amount * sign

                if (
                    rec.currency_id
                    and rec.company_id
                    and rec.currency_id != rec.company_id.currency_id
                ):
                    cur = rec.currency_id
                    amount_uninvoiced = cur.round(amount_uninvoiced)

                amount_uninvoiced_company = (
                    rec._compute_amount_uninvoiced_company_currency(amount_uninvoiced)
                )
                payment_terms = rec._compute_payment_terms(
                    rec.expected_date,
                    amount_uninvoiced_company,
                    amount_uninvoiced,
                )

                payment_term_count = len(payment_terms)
                payment_term_line = 0

                for payment_term in payment_terms:
                    payment_term_line += 1
                    new_vals = rec._prepare_mis_cash_flow_forecast_line(
                        payment_term_line,
                        payment_term_count,
                        payment_term[0],
                        payment_term[1],
                    )
                    values.append(new_vals)

        return self.env["mis.cash_flow.forecast_line"].create(values)

    @api.model
    def cron_mis_cash_flow_generate_forecast_lines(self):
        offset = 0
        while True:
            orders = self.search(
                [
                    ("forecast_uninvoiced_amount", ">", 0),
                    ("state", "in", ["sale", "done"]),
                ],
                limit=100,
                offset=offset,
            )
            orders.with_delay()._generate_mis_cash_flow_forecast_lines()
            if len(orders) < 100:
                break
            offset += 100

    def action_show_mis_forecast(self):
        self.ensure_one()
        context = dict(self.env.context)
        context.pop("group_by", None)

        return {
            "type": "ir.actions.act_window",
            "name": _("Cash Flow Forecast - Sale"),
            "res_model": "mis.cash_flow.forecast_line",
            "domain": [
                ("parent_res_model", "=", self._name),
                ("parent_res_id", "=", self.id),
            ],
            "view_mode": "pivot,tree",
            "context": context,
        }
