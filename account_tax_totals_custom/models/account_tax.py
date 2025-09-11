# Copyright 2025 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools.misc import formatLang


class AccountTax(models.Model):

    _inherit = "account.tax"

    @api.model
    def _prepare_tax_totals(self, base_lines, currency, tax_lines=None):
        res = super()._prepare_tax_totals(base_lines, currency, tax_lines)
        res["formatted_amount_total"] = formatLang(
            self.env,
            sum(line["price_subtotal"] for line in base_lines),
            currency_obj=currency,
        )
        return res
