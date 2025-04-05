# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountCompensateAdvanceJournal(models.TransientModel):
    _name = "account.compensate.advance.journal"
    _description = "Advance Compensation Journal Wizard"

    # Advance Fields #
    advance_id = fields.Many2one(
        "account.move.line",
        string="Advance Line",
        domain=lambda self: self._get_domain_advance_id(),
        required=True,
    )
    advance_balance = fields.Monetary(
        currency_field="currency_id",
        compute="_compute_advance_balance",
    )
    # Invoice Fields #
    line_id = fields.Many2one(
        "account.move.line",
        domain=lambda self: self._get_domain_line_id(),
        required=True,
    )
    amount = fields.Monetary(
        currency_field="currency_id",
        readonly=False,
    )
    # Compensation Fields #
    journal_id = fields.Many2one(
        "account.journal",
        string="Compesation Journal",
        domain=[("is_advance_journal", "=", True)],
        required=True,
    )
    # Currency #
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        store=True,
        readonly=False,
        compute="_compute_currency_id",
    )
    date = fields.Date(string="Compensation Date")

    @api.onchange("line_id")
    def _onchange_line_id(self):
        """
        Onchange handler for line_id field.
        Updates the amount field based on the residual amount of the selected invoice line.
        """
        self.amount = abs(self.line_id.amount_residual) if self.line_id else 0

    @api.depends("journal_id")
    def _compute_currency_id(self):
        """
        Computes the currency_id based on the journal's currency.
        If the journal does not have a currency, it defaults to the company's currency.
        """
        self.currency_id = (
            self.journal_id.currency_id or self.journal_id.company_id.currency_id
        )

    @api.depends("advance_id")
    def _compute_advance_balance(self):
        """
        Computes the advance_balance based on the residual amount of the selected advance line.
        """
        self.advance_balance = (
            abs(self.advance_id.amount_residual) if self.advance_id else 0
        )

    @api.model
    def _get_domain_advance_id(self):
        move = self.env["account.move"].browse(self.env.context.get("active_ids", []))
        if not move or not move.partner_id:
            return [("id", "=", 0)]

        domain = [
            ("move_id.payment_state", "=", "paid"),
            ("partner_id", "=", move.partner_id.id),
            ("account_id.account_type", "=", "asset_prepayments"),
            ("account_id.reconcile", "=", True),
        ]

        if move.move_type == "in_invoice":
            domain.append(("amount_residual", ">", 0.0))
        elif move.move_type == "out_invoice":
            domain.append(("amount_residual", "<", 0.0))

        return domain

    @api.model
    def _get_domain_line_id(self):
        active_ids = self.env.context.get("active_ids", [])
        if not active_ids:
            return [("id", "=", 0)]

        move_type = self.env.context.get("default_move_type")
        domain = [
            ("move_id", "in", active_ids),
            ("amount_residual", "!=", 0.0),
        ]

        account_type = None
        if move_type == "out_invoice":
            account_type = "asset_receivable"
        elif move_type == "in_invoice":
            account_type = "liability_payable"

        if account_type:
            domain.append(("account_id.account_type", "=", account_type))

        return domain

    def _create_compensate_advance_account(self):
        """
        Main method to create a journal entry to compensate an advance payment.
        """
        params = self._prepare_compensation_params()

        self._validate_compensation_amount(params["amount"], params["line_id"])

        move_vals = self._prepare_move_vals(params)

        move = (
            self.env["account.move"].with_context(**self.env.context).create(move_vals)
        )
        move.action_post()

        # Reconciliation
        self._create_advance_reconciliation(params["line_id"] + move.line_ids[0])
        self._create_advance_reconciliation(self.advance_id + move.line_ids[1])

    def _prepare_compensation_params(self):
        """
        Prepares the parameters for the compensation account move.
        """
        move_id = self.env["account.move"].browse(self.env.context.get("active_ids"))
        move_type = self.env.context.get("default_move_type")

        params = {
            "move_type": move_type,
            "move_id": move_id,
            "partner_id": move_id.partner_id,
            "journal_id": self.journal_id,
            "advance_id": self.advance_id,
            "line_id": self.line_id,
            "amount": self.amount,
            "compensation_date": self.date or fields.Date.today(),
        }
        return params

    def _validate_compensation_amount(self, amount, line_id):
        """
        Validates the compensation amount before creating the move.
        """
        if amount <= 0:
            raise ValidationError(_("The amount must be greater than zero."))
        if amount > abs(line_id.amount_residual):
            raise ValidationError(
                _("The amount cannot exceed the residual amount of the line.")
            )
        if amount > self.advance_balance:
            raise ValidationError(
                _("The entered amount exceeds the balance of the advance selected.")
            )

    def _prepare_move_vals(self, params):
        """
        Prepares the values for the account move.
        """
        credit_vals, debit_vals = self._prepare_move_lines(params)

        advance_str = _("Advance: %s") % params["move_id"].name

        move_vals = {
            "move_type": "entry",
            "partner_id": params["partner_id"].id,
            "ref": advance_str,
            "journal_id": params["journal_id"].id,
            "date": params["compensation_date"],
            "line_ids": [(0, 0, credit_vals), (0, 0, debit_vals)],
        }

        return move_vals

    def _prepare_move_lines(self, params):
        """
        Prepare the debit and credit lines for the journal entry based on the parameters.

        :param params: A dictionary containing parameters for the move lines.
        :return: A tuple containing the credit and debit line values.
        """
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
                    "account_id": params["advance_id"].account_id.id,
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
                    "account_id": params["advance_id"].account_id.id,
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
        """
        Action to initiate the advance compensation process.
        Calls the method to create the compensation account move.
        """
        res = self._create_compensate_advance_account()
        return res

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        """
        Override the fields_view_get method to modify
        the view fields dynamically based on context.

        Args:
            view_id (int): ID of the view.
            view_type (str): Type of the view ('form', 'tree', 'kanban', etc.).
            toolbar (bool): Flag indicating whether the toolbar is visible.
            submenu (bool): Flag indicating whether the submenu is visible.

        Returns:
            dict: Updated result of fields_view_get with modified fields based on context.
        """
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )

        # Modify fields based on the view type being 'form'
        if view_type == "form":
            # Set context for 'advance_id' field if present in the view fields
            if "advance_id" in res["fields"]:
                res["fields"]["advance_id"]["context"] = {"advance_id_name_get": True}

            # Set context for 'line_id' field if present in the view fields
            if "line_id" in res["fields"]:
                res["fields"]["line_id"]["context"] = {"line_id_name_get": True}

        return res
