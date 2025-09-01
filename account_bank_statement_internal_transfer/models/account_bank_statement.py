# Copyright 2025 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    payment_ids = fields.One2many(
        comodel_name="account.payment",
        compute="_compute_payment_ids",
        readonly=True,
    )
    payment_count = fields.Integer(compute="_compute_payment_count")

    @api.depends("line_ids")
    def _compute_payment_ids(self):
        for statement in self:
            statement.payment_ids = self.line_ids.mapped("payment_id")

    @api.depends("payment_ids")
    def _compute_payment_count(self):
        for statement in self:
            statement.payment_count = len(statement.payment_ids)

    def button_account_payments(self):
        return {
            "name": _("Payments"),
            "view_mode": "tree,form",
            "res_model": "account.payment",
            "view_id": False,
            "type": "ir.actions.act_window",
            "domain": [("id", "in", self.payment_ids.ids)],
        }
