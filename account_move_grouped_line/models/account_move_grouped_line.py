# Copyright 2025 Marcel Savegnago <https://escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveGroupedLine(models.Model):
    _name = "account.move.grouped.line"
    _description = "Account Move Grouped Line"

    account_id = fields.Many2one("account.account", string="Account")
    account_move_id = fields.Many2one("account.move", string="Journal Entry")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id.id,
    )
    name = fields.Char(related="account_id.name")
    debit = fields.Monetary(currency_field="currency_id")
    credit = fields.Monetary(currency_field="currency_id")
