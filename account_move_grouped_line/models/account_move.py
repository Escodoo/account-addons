# Copyright 2025 Marcel Savegnago <https://escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    grouped_items_id = fields.One2many(
        "account.move.grouped.lines",
        "account_move_id",
        compute="_compute_grouped_items",
    )

    def _compute_grouped_items(self):
        """create records at 'grouped.itens' based on 'line_ids'"""
        for record in self:
            grouped_aml = self.env["account.move.line"].read_group(
                domain=[("move_id", "=", record.id)],
                fields=[],
                groupby=[
                    "account_id",
                    "name",
                    "analytic_account_id",
                    "analytic_tag_ids",
                    "tax_ids",
                ],
            )

            grouped_item_lines = [
                {
                    "account_move_id": record.id,
                    "account_id": line.get("account_id")[0],
                    "credit": line.get("credit"),
                    "debit": line.get("debit"),
                }
                for line in grouped_aml
            ]
            grouped_lines_ids = self.env["account.move.grouped.lines"].create(
                grouped_item_lines
            )
            record.grouped_items_id = [(6, 0, grouped_lines_ids.ids)]
