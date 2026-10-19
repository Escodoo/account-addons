# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models


class Contract(models.Model):
    _inherit = "contract.contract"

    @api.model
    def _get_mis_cash_flow_forecast_update_trigger_fields(self):
        return [
            "partner_id",
            "pricelist_id",
            "fiscal_position_id",
            "currency_id",
            "contract_line_ids",
        ]

    def _prepare_mis_cash_flow_forecast_line_values(self):
        res = []
        for rec in self:
            if rec.company_id.enable_contract_mis_cash_flow_forecast:
                for line in rec.contract_line_ids:
                    if (
                        line.next_period_date_end
                        and line.recurring_next_date
                        and line._get_generate_mis_cash_flow_forecast_line_criteria(
                            line.next_period_date_end
                        )
                    ):
                        res.append(
                            line._prepare_mis_cash_flow_forecast_line(
                                line.next_period_date_start,
                                line.next_period_date_end,
                                line.recurring_next_date,
                            )
                        )
        return res

    def write(self, values):
        result = super().write(values)
        if set(values).intersection(
            self._get_mis_cash_flow_forecast_update_trigger_fields()
        ):
            for contract in self:
                contract.contract_line_ids.with_delay()._generate_mis_cash_flow_forecast_lines()
        return result

    def unlink(self):
        for rec in self:
            for line in rec.contract_line_ids:
                if line.mis_cash_flow_forecast_line_ids:
                    line.mis_cash_flow_forecast_line_ids.unlink()
        return super().unlink()

    def action_show_mis_forecast(self):
        self.ensure_one()
        context = dict(self.env.context)
        context.pop("group_by", None)

        return {
            "type": "ir.actions.act_window",
            "name": _("Cash Flow Forecast - Contract"),
            "res_model": "mis.cash_flow.forecast_line",
            "domain": [
                ("parent_res_model", "=", self._name),
                ("parent_res_id", "=", self.id),
            ],
            "view_mode": "pivot,list",
            "context": context,
        }
