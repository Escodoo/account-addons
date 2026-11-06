# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ContractLine(models.Model):
    _inherit = "contract.line"

    mis_cash_flow_forecast_line_ids = fields.One2many(
        comodel_name="mis.cash_flow.forecast_line",
        compute="_compute_mis_cash_flow_forecast_line_ids",
        string="Forecast Lines",
    )

    mis_cash_flow_forecast_line_count = fields.Integer(
        compute="_compute_mis_cash_flow_forecast_line_ids",
        string="Forecast Line Count",
    )

    def _compute_mis_cash_flow_forecast_line_ids(self):
        ForecastLine = self.env["mis.cash_flow.forecast_line"]
        if not self:
            return
        res_model = self.env["ir.model"]._get(self._name)
        forecast_lines = ForecastLine.search(
            [("res_model_id", "=", res_model.id), ("res_id", "in", self.ids)]
        )
        result = dict.fromkeys(self.ids, ForecastLine)
        for forecast in forecast_lines:
            result[forecast.res_id] |= forecast
        for rec in self:
            rec.mis_cash_flow_forecast_line_ids = result[rec.id]
            rec.mis_cash_flow_forecast_line_count = len(result[rec.id])

    def _get_mis_cash_flow_forecast_lines(self):
        return self.env["mis.cash_flow.forecast_line"].search(
            [
                ("res_model_id", "=", self.env["ir.model"]._get(self._name).id),
                ("res_id", "in", self.ids),
            ]
        )

    def _get_mis_cash_flow_forecast_account(self, field_name):
        """Return the partner account of the contract used for the forecast.

        Since 18.0 an account can be shared between several companies
        (``company_ids``), so the account of the contract partner is only
        usable when the contract company belongs to it. Fallback on the
        account of the company partner, as in the former ``company_id``
        based check.
        """
        self.ensure_one()
        company = self.contract_id.company_id
        account = self.contract_id.partner_id.with_company(company)[field_name]
        if account and company not in account.company_ids:
            account = company.partner_id.with_company(company)[field_name]
        return account

    def _prepare_mis_cash_flow_forecast_line(
        self, period_date_start, period_date_end, recurring_next_date
    ):
        self.ensure_one()
        contract = self.contract_id
        sign = contract.contract_type in ["purchase"] and -1 or 1
        subtotal = self.quantity * self.price_unit
        discount = self.discount / 100
        subtotal *= 1 - discount
        price_subtotal_signed = subtotal * sign
        price_subtotal_company_signed = price_subtotal_signed
        if (
            contract.currency_id
            and contract.company_id
            and contract.currency_id != contract.company_id.currency_id
        ):
            cur = contract.currency_id
            price_subtotal = cur.round(subtotal)
            price_subtotal_signed = cur.round(price_subtotal_signed)
            rate_date = recurring_next_date or fields.Date.today()
            price_subtotal_company = cur._convert(
                price_subtotal,
                contract.company_id.currency_id,
                contract.company_id,
                rate_date,
            )
            price_subtotal_company_signed = price_subtotal_company * sign

        if contract.contract_type == "sale":
            account_id = self._get_mis_cash_flow_forecast_account(
                "property_account_receivable_id"
            )
        else:
            account_id = self._get_mis_cash_flow_forecast_account(
                "property_account_payable_id"
            )

        parent_res_id = contract
        parent_res_model_id = self.env["ir.model"]._get(parent_res_id._name)

        period_label = self._insert_markers(period_date_start, period_date_end)
        return {
            "name": f"{contract.display_name} - {period_label}",
            "date": recurring_next_date,
            "account_id": account_id.id,
            "partner_id": contract.partner_id.id,
            "balance": price_subtotal_company_signed,
            "company_id": contract.company_id.id,
            "res_model_id": self.env["ir.model"]._get(self._name).id,
            "res_id": self.id,
            "parent_res_model_id": parent_res_model_id.id,
            "parent_res_id": parent_res_id.id,
        }

    def _get_mis_cash_flow_contract_forecast_end_date(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        company = self.contract_id.company_id
        return today + self.get_relative_delta(
            company.contract_mis_cash_flow_forecast_rule_type,
            company.contract_mis_cash_flow_forecast_interval,
        )

    def _get_generate_mis_cash_flow_forecast_line_criteria(self, period_date_end):
        self.ensure_one()
        if not self.contract_id.company_id.enable_contract_mis_cash_flow_forecast:
            return False
        if self.is_canceled or not self.active:
            return False
        contract_forecast_end_date = (
            self._get_mis_cash_flow_contract_forecast_end_date()
        )
        if not self.date_end:
            return period_date_end < contract_forecast_end_date
        return (
            period_date_end <= self.date_end
            and period_date_end <= contract_forecast_end_date
        )

    def _generate_mis_cash_flow_forecast_lines(self):
        """Generate forecast lines for contract lines based on recurring periods."""
        ForecastLine = self.env["mis.cash_flow.forecast_line"]
        values = []

        # Delete existing forecast lines for these contract lines
        self._get_mis_cash_flow_forecast_lines().unlink()

        for rec in self:
            if not rec.recurring_next_date:
                continue
            period_date_start = rec.next_period_date_start
            period_date_end = rec.next_period_date_end
            recurring_next_date = rec.recurring_next_date
            max_date_end = rec.date_end

            while (
                period_date_end
                and rec._get_generate_mis_cash_flow_forecast_line_criteria(
                    period_date_end
                )
            ):
                if recurring_next_date:
                    new_vals = rec._prepare_mis_cash_flow_forecast_line(
                        period_date_start,
                        period_date_end,
                        recurring_next_date,
                    )
                    values.append(new_vals)

                period_date_start = period_date_end + relativedelta(days=1)
                period_date_end = rec.get_next_period_date_end(
                    period_date_start,
                    rec.recurring_rule_type,
                    rec.recurring_interval,
                    max_date_end=max_date_end,
                )
                recurring_next_date = rec.get_next_invoice_date(
                    period_date_start,
                    rec.recurring_invoicing_type,
                    rec.recurring_invoicing_offset,
                    rec.recurring_rule_type,
                    rec.recurring_interval,
                    max_date_end=max_date_end,
                )

        forecast_lines = ForecastLine.create(values)
        # The forecast lines live in another model: the computed fields are not
        # invalidated by their creation, so drop any value cached earlier in
        # the transaction (forecast line count/ids read before the generation).
        self.invalidate_recordset(
            ["mis_cash_flow_forecast_line_ids", "mis_cash_flow_forecast_line_count"]
        )
        return forecast_lines

    @api.model_create_multi
    def create(self, vals_list):
        contract_lines = super().create(vals_list)
        for contract_line in contract_lines:
            company = contract_line.contract_id.company_id
            if company.enable_contract_mis_cash_flow_forecast:
                contract_line.with_delay()._generate_mis_cash_flow_forecast_lines()
        return contract_lines

    @api.model
    def _get_mis_cash_flow_forecast_update_trigger_fields(self):
        return [
            "name",
            "sequence",
            "product_id",
            "date_start",
            "date_end",
            "quantity",
            "price_unit",
            "discount",
            "recurring_invoicing_type",
            "recurring_next_date",
            "recurring_rule_type",
            "recurring_interval",
            "is_canceled",
            "active",
        ]

    def write(self, values):
        res = super().write(values)
        trigger_fields = self._get_mis_cash_flow_forecast_update_trigger_fields()
        if any([field in values for field in trigger_fields]):
            for rec in self:
                company = rec.contract_id.company_id
                if company.enable_contract_mis_cash_flow_forecast:
                    rec.with_delay()._generate_mis_cash_flow_forecast_lines()
        return res

    def unlink(self):
        """Delete related forecast lines before deleting contract lines."""
        self._get_mis_cash_flow_forecast_lines().unlink()
        return super().unlink()

    @api.model
    def cron_mis_cash_flow_generate_forecast_contract_lines(self):
        """Cron job to regenerate forecast lines for all active contract lines."""
        offset = 0
        contract_lines_env = self.env["contract.line"]
        while True:
            contract_lines = contract_lines_env.search(
                [("is_canceled", "=", False)],
                limit=25,
                offset=offset,
            ).filtered(lambda x: x.create_invoice_visibility)

            if contract_lines:
                contract_lines.with_delay()._generate_mis_cash_flow_forecast_lines()

            if len(contract_lines) < 25:
                break
            offset += 25
