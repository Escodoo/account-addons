# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountCompensateAdvanceJournal(models.TransientModel):
    _name = "account.compensate.advance.journal"

    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        domain=lambda self: self._get_domain_journal_id(),
        required=True,
    )
    advance_id = fields.Many2one(
        "account.move",
        string="Journal Entry",
        domain=lambda self: self._get_domain_advance_id(),
        required=True,
    )
    line_id = fields.Many2one(
        "account.move.line",
        domain=lambda self: self._get_domain_line_id(),
        required=True,
    )
    entry_date = fields.Date(
        string="Entry Date",
        default=lambda self: self._get_entry_date(),
        readonly=False,
        required=True,
    )
    amount = fields.Monetary(
        currency_field="currency_id",
        readonly=False,
    )
    advance_balance = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_advance_balance",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        store=True,
        readonly=False,
        compute="_compute_currency_id",
    )

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        if self.journal_id:
            return {"domain": {"advance_id": self._get_domain_advance_id()}}

    @api.onchange("line_id")
    def _onchange_line_id(self):
        self.amount = abs(self.line_id.amount_residual) if self.line_id else 0

    @api.model
    def _get_entry_date(self):
        move_id = self.env.context.get("active_ids")
        if move_id:
            move = self.env["account.move"].browse(move_id[0])
            return (
                move.invoice_date.strftime("%Y-%m-%d")
                if move.invoice_date
                else fields.Date.today().strftime("%Y-%m-%d")
            )
        return fields.Date.today().strftime("%Y-%m-%d")

    @api.model
    def _get_domain_journal_id(self):
        move_type = self.env.context.get("default_move_type")
        domain = [("is_advance_journal", "=", True)]
        if move_type == "out_invoice":
            domain.append(("advance_account_type", "=", "customer"))
        elif move_type == "in_invoice":
            domain.append(("advance_account_type", "=", "supplier"))
        return domain

    @api.model
    def _get_domain_advance_id(self):
        domain = [("journal_id", "=", self.journal_id.id)]
        move_type = self.env.context.get("default_move_type")
        move = self.env["account.move"].browse(self.env.context.get("active_ids"))
        partner_id = move.partner_id.id

        if move_type in ["out_invoice", "in_invoice"]:
            domain.extend(
                [
                    ("is_advance_move", "=", True),
                    ("line_ids.partner_id", "=", partner_id),
                    ("line_ids.amount_residual", ">", 0.0),
                    ("line_ids.amount_residual", "<", 0.0),
                ]
            )

        return domain

    @api.model
    def _get_domain_line_id(self):
        move_id = self.env.context.get("active_ids")
        move_type = self.env.context.get("default_move_type")
        domain = [
            ("move_id", "in", move_id),
            ("amount_residual", "!=", 0.0),
        ]

        if move_type == "out_invoice":
            domain.append(("account_id.user_type_id.type", "=", "receivable"))
        elif move_type == "in_invoice":
            domain.append(("account_id.user_type_id.type", "=", "payable"))

        return domain

    @api.depends("journal_id")
    def _compute_currency_id(self):
        self.currency_id = (
            self.journal_id.currency_id or self.journal_id.company_id.currency_id
        )

    @api.depends("advance_id")
    def _compute_advance_balance(self):
        self.advance_balance = (
            abs(self.advance_id.line_ids[0].amount_residual) if self.advance_id else 0
        )

    @api.constrains("amount")
    def _check_amount(self):
        if self.amount <= 0:
            raise ValidationError(_("The amount must be greater than zero."))
        if self.amount > abs(self.line_id.amount_residual):
            raise ValidationError(
                _("The amount cannot exceed the residual amount of the line.")
            )

    def _create_compensate_advance_account(self):
        move_id = self.env["account.move"].browse(self.env.context.get("active_ids"))
        move_type = self.env.context.get("default_move_type")
        amount = self.amount
        partner_id = move_id.partner_id
        journal_id = self.journal_id
        line_id = self.line_id

        params = {
            "move_type": move_type,
            "move_id": move_id,
            "partner_id": partner_id,
            "journal_id": journal_id,
            "line_id": line_id,
            "amount": amount,
        }

        credit_vals, debit_vals = self._prepare_move_lines(params)

        move_vals = {
            "move_type": "entry",
            "partner_id": partner_id.id,
            "ref": _("Advance: %s" % move_id.name),
            "journal_id": journal_id.id,
            "date": self.entry_date,
            "line_ids": [(0, 0, credit_vals), (0, 0, debit_vals)],
        }
        if amount > self.advance_balance:
            raise ValidationError(
                _("The entered amount exceeds the balance of the advance selected.")
            )
        move = self.env["account.move"].create(move_vals)
        move.post()

        self._create_advance_reconciliation(line_id + move.line_ids[0])
        self._create_advance_reconciliation(
            self.advance_id.line_ids[0] + move.line_ids[1]
        )

    def _prepare_move_lines(self, params):
        base_vals = {
            "name": params["move_id"].name,
            "partner_id": params["partner_id"].id,
            "account_id": params["line_id"].account_id.id,
        }

        if params["move_type"] == "in_invoice":
            credit_vals = base_vals.copy()
            credit_vals.update({"credit": 0.0, "debit": params["amount"]})
            debit_vals = base_vals.copy()
            debit_vals.update(
                {
                    "account_id": params["journal_id"].advance_account_supplier_id.id,
                    "credit": params["amount"],
                    "debit": 0.0,
                }
            )
        elif params["move_type"] == "out_invoice":
            credit_vals = base_vals.copy()
            credit_vals.update({"credit": params["amount"], "debit": 0.0})
            debit_vals = base_vals.copy()
            debit_vals.update(
                {
                    "account_id": params["journal_id"].advance_account_customer_id.id,
                    "credit": 0.0,
                    "debit": params["amount"],
                }
            )

        return credit_vals, debit_vals

    def _create_advance_reconciliation(self, line_ids):
        """
        Perform reconciliation for the provided account.move.line records.

        :param line_ids: account.move.line records to reconcile.
        """
        line_ids.reconcile()

    def action_compensate_advance_account(self):
        res = self._create_compensate_advance_account()
        return res
