# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountCreateAdvanceJournal(models.TransientModel):
    _name = "account.create.advance.journal"

    amount = fields.Monetary(currency_field="currency_id", required=True)
    currency_id = fields.Many2one("res.currency", string="Journal Currency")
    date_maturity = fields.Date(
        string="Date Maturity",
    )
    date = fields.Date(
        string="Account Date",
        required=True,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        domain=lambda self: self._get_domain_journal_id(),
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        required=True,
    )

    @api.model
    def _get_domain_journal_id(self):
        move_type = self.env.context.get("move_type")
        if move_type == "out_invoice":
            return [
                ("is_advance_journal", "=", True),
                ("advance_account_type", "=", "customer"),
            ]
        elif move_type == "in_invoice":
            return [
                ("is_advance_journal", "=", True),
                ("advance_account_type", "=", "supplier"),
            ]

    @api.constrains("amount")
    def _constrain_amount(self):
        for rec in self:
            if rec.amount <= 0.0:
                raise ValidationError(_("The amount must always be positive."))

    def _create_advance_account(self):
        move_type = self._context.get("move_type")
        partner_id = self.partner_id
        amount = self.amount
        date = self.date
        date_maturity = self.date_maturity or False
        journal_id = self.journal_id

        if move_type == "in_invoice":
            debit_vals = {
                "partner_id": partner_id.id,
                "account_id": journal_id.advance_account_supplier_id.id,
                "debit": amount,
                "credit": 0.0,
            }
            credit_vals = {
                "partner_id": partner_id.id,
                "account_id": partner_id.property_account_payable_id.id,
                "debit": 0.0,
                "credit": amount,
                "date_maturity": date_maturity,
            }

        elif move_type == "out_invoice":
            debit_vals = {
                "partner_id": partner_id.id,
                "account_id": journal_id.advance_account_customer_id.id,
                "debit": 0.0,
                "credit": amount,
            }
            credit_vals = {
                "partner_id": partner_id.id,
                "account_id": partner_id.property_account_receivable_id.id,
                "debit": amount,
                "credit": 0.00,
                "date_maturity": date_maturity,
            }

        move_vals = {
            "is_advance_move": True,
            "partner_id": partner_id.id,
            "journal_id": journal_id.id,
            "date": date,
            "line_ids": [(0, 0, debit_vals), (0, 0, credit_vals)],
        }

        move = self.env["account.move"].create(move_vals)
        move.post()

        return move

    def action_create_advance_account(self):

        move = self._create_advance_account()

        return {
            "name": _("Journal Entry"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": move.id,
            "target": "current",
        }
