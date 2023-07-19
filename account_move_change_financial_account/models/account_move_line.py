# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from odoo import api, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    # @api.model_create_multi
    # def create(self, vals_list):
    #     lines_super = super().create(vals_list)
    #     self._apply_financial_rules(lines_super)
    #     return lines_super

    def _get_financial_lines(self, lines):
        return lines.filtered(
            lambda line: line.account_id.user_type_id.type in ("receivable", "payable")
        )

    def _apply_financial_rules(self, lines):
        financial_lines = self._get_financial_lines(lines)

        if not financial_lines:
            return

        domain_ids = self.env["account.account.financial.rules"].search(
            [("domain", "!=", False)]
        )

        for domain_id in domain_ids:
            if not financial_lines:
                break

            domain = ast.literal_eval(domain_id.domain)
            lines_to_change = financial_lines.filtered_domain(domain)

            if lines_to_change:
                for line in lines_to_change:
                    line.account_id = domain_id.financial_account_id
                financial_lines -= lines_to_change
