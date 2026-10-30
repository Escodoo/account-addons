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

    def unlink(self):
        self.contract_line_ids._get_mis_cash_flow_forecast_lines().unlink()
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
