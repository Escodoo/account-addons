# Copyright 2025 Marcel Savegnago <https://escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveGroupedLine(models.Model):
    _name = "account.move.grouped.line"
    _description = "Account Move Grouped Line"

    account_id = fields.Many2one("account.account")
    account_move_id = fields.Many2one("account.move")
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id.id
    )
    name = fields.Char(related="account_id.name")
    analytic_account_id = fields.Many2one("account.analytic.account")
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")
    tax_ids = fields.Many2many("account.tax", string="Taxes")
    credit = fields.Monetary(currency_field="currency_id")
    debit = fields.Monetary(currency_field="currency_id")
