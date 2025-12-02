# Copyright 2025 Marcel Savegnago <https://escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    grouped_items_id = fields.One2many(
        "account.move.grouped.line",
        "account_move_id",
        compute="_compute_grouped_items",
    )

    def _compute_grouped_items(self):
        """Create records at 'account.move.grouped.line' based on 'line_ids'."""
        GroupedLine = self.env["account.move.grouped.line"]
        for record in self:
            # Group lines by account using ORM instead of read_group
            # read_group uses direct SQL which may not see uncommitted records
            grouped_data = {}
            for line in record.line_ids:
                if line.account_id:
                    account_id = line.account_id.id
                    if account_id not in grouped_data:
                        grouped_data[account_id] = {"debit": 0.0, "credit": 0.0}
                    grouped_data[account_id]["debit"] += line.debit
                    grouped_data[account_id]["credit"] += line.credit

            grouped_item_lines = [
                {
                    "account_move_id": record.id,
                    "account_id": account_id,
                    "debit": values["debit"],
                    "credit": values["credit"],
                }
                for account_id, values in grouped_data.items()
            ]
            if grouped_item_lines:
                record.grouped_items_id = GroupedLine.create(grouped_item_lines)
            else:
                record.grouped_items_id = GroupedLine
