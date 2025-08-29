# Copyright 2025 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    payment_id = fields.Many2one(
        comodel_name="account.payment",
        readonly=True,
    )
    payment_ids = fields.Many2one(
        comodel_name="account.payment",
        inverse_name="reconciled_statement_line_ids",
        readonly=True,
    )

    def action_open_internal_transfer(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account_bank_statement_internal_transfer.internal_transfer_wizard_action"
        )
        action["context"] = {
            "active_id": self.id,
            "company_id": self.company_id.id,
            "journal_id": self.statement_id.journal_id.id,
            "amount": self.amount,
            "currency_id": self.currency_id.id,
            "date": self.date,
            "ref": self.payment_ref,
        }
        return action
