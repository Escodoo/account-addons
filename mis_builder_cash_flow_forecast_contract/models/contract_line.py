# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ContractLine(models.Model):

    _inherit = "contract.line"

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

    def _prepare_mis_cash_flow_forecast_line(
        self, period_date_start, period_date_end, recurring_next_date
    ):
        self.ensure_one()
        sign = self.contract_id.contract_type in ["purchase"] and -1 or 1
        subtotal = self.quantity * self.price_unit
        discount = self.discount / 100
        subtotal *= 1 - discount
        price_subtotal_signed = subtotal * sign
        price_subtotal_company_signed = price_subtotal_signed
        if (
            self.contract_id.currency_id
            and self.contract_id.company_id
            and self.contract_id.currency_id != self.contract_id.company_id.currency_id
        ):
            cur = self.contract_id.currency_id
            price_subtotal = cur.round(subtotal)
            price_subtotal_signed = cur.round(price_subtotal_signed)
            rate_date = recurring_next_date or fields.Date.today()
            price_subtotal_company = cur._convert(
                price_subtotal,
                self.contract_id.company_id.currency_id,
                self.contract_id.company_id,
                rate_date,
            )
            price_subtotal_company_signed = price_subtotal_company * sign

        partner = self.contract_id.partner_id.with_company(
            self.contract_id.company_id.id
        )

        if self.contract_id.contract_type == "sale":
            account_id = partner.property_account_receivable_id.id
        elif self.contract_id.contract_type == "purchase":
            account_id = partner.property_account_payable_id.id

        parent_res_id = self.contract_id
        parent_res_model_id = self.env["ir.model"]._get(parent_res_id._name)

        return {
            "name": "%s - %s"
            % (
                self.contract_id.display_name,
                self._insert_markers(period_date_start, period_date_end),
            ),
            "date": recurring_next_date,
            "account_id": account_id,
            "partner_id": self.contract_id.partner_id.id,
            "balance": price_subtotal_company_signed,
            "company_id": self.contract_id.company_id.id,
            "res_model_id": self.env["ir.model"]._get(self._name).id,
            "res_id": self.id,
            "parent_res_model_id": parent_res_model_id.id,
            "parent_res_id": parent_res_id.id,
        }

    def _get_mis_cash_flow_contract_forecast_end_date(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        return today + self.get_relative_delta(
            self.contract_id.company_id.contract_mis_cash_flow_forecast_rule_type,
            self.contract_id.company_id.contract_mis_cash_flow_forecast_interval,
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
        if not self.date_end or self.is_auto_renew:
            return period_date_end < contract_forecast_end_date
        return (
            period_date_end <= self.date_end
            and period_date_end <= contract_forecast_end_date
        )

    def _generate_mis_cash_flow_forecast_lines(self):
        values = []
        for rec in self:
            rec.mis_cash_flow_forecast_line_ids.unlink()
            if rec.recurring_next_date:
                period_date_start = rec.next_period_date_start
                period_date_end = rec.next_period_date_end
                recurring_next_date = rec.recurring_next_date
                max_date_end = rec.date_end if not rec.is_auto_renew else False
                while (
                    period_date_end
                    and rec._get_generate_mis_cash_flow_forecast_line_criteria(
                        period_date_end
                    )
                ):
                    if period_date_end and recurring_next_date:
                        new_vals = rec._prepare_mis_cash_flow_forecast_line(
                            period_date_start,
                            period_date_end,
                            recurring_next_date,
                        )
                        values.append(new_vals)
                    period_date_start = period_date_end + relativedelta(days=1)
                    period_date_end = self.get_next_period_date_end(
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

        return self.env["mis.cash_flow.forecast_line"].create(values)

    @api.model
    def create(self, values):
        contract_lines = super(ContractLine, self).create(values)
        for contract_line in contract_lines:
            if (
                contract_line.contract_id.company_id.enable_contract_mis_cash_flow_forecast
            ):
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
            "is_auto_renew",
        ]

    def write(self, values):
        res = super(ContractLine, self).write(values)
        if any(
            [
                field in values
                for field in self._get_mis_cash_flow_forecast_update_trigger_fields()
            ]
        ):
            for rec in self:
                if rec.contract_id.company_id.enable_contract_mis_cash_flow_forecast:
                    rec.with_delay()._generate_mis_cash_flow_forecast_lines()
        return res

    def unlink(self):
        for rec in self:
            if rec.mis_cash_flow_forecast_line_ids:
                rec.mis_cash_flow_forecast_line_ids.unlink()
        return super().unlink()

    @api.model
    def cron_mis_cash_flow_generate_forecast_contract_lines(self):
        offset = 0
        while True:
            contract_lines = self.search(
                [("is_canceled", "=", False)], limit=25, offset=offset
            )
            contract_lines.with_delay()._generate_mis_cash_flow_forecast_lines()
            if len(contract_lines) < 25:
                break
            offset += 25

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
