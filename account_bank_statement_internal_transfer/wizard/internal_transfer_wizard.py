# Copyright 2025 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class InternalTransferWizard(models.TransientModel):
    _name = "internal.transfer.wizard"
    _description = "Internal Transfer Wizard"

    def _get_destination_journal_domain(self):
        journal_id = self.env.context.get("journal_id")
        return [("type", "in", ("bank", "cash")), ("id", "!=", journal_id)]

    def _default_transfer_type(self):
        if self.env.context.get("amount", 0.0) < 0.0:
            return "outbound"
        return "inbound"

    transfer_type = fields.Selection(
        selection=[
            ("inbound", "Inbound"),
            ("outbound", "Outbound"),
        ],
        default=_default_transfer_type,
        readonly=True,
        help="Given by the sign of the statement line amount: positive is an "
        "inbound transfer, negative is an outbound one.",
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Statement Journal",
        default=lambda self: self.env.context.get("journal_id"),
        readonly=True,
    )
    amount = fields.Monetary(
        default=lambda self: abs(self.env.context.get("amount", 0.0)),
        readonly=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.context.get("currency_id"),
        readonly=True,
    )
    destination_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Other Journal",
        domain=_get_destination_journal_domain,
        help="The other bank or cash journal of the transfer: where the money "
        "comes from on an inbound transfer, or where it goes on an outbound one.",
    )

    def _get_payment_method_line(self, payment_type):
        journal = self.env["account.journal"].browse(self.env.context["journal_id"])
        if payment_type == "inbound":
            lines = journal.inbound_payment_method_line_ids
        else:
            lines = journal.outbound_payment_method_line_ids
        lines = lines.filtered(lambda x: x.code not in ("240", "400", "500"))
        return lines.filtered(lambda x: x.code == "manual")[:1] or lines[:1]

    def action_create_internal_transfer(self):
        context = self.env.context

        payment_type = "outbound" if context["amount"] < 0.0 else "inbound"
        payment_amount = abs(context["amount"])

        payment_id = self.env["account.payment"].create(
            {
                "name": "/",
                "company_id": context["company_id"],
                "payment_type": payment_type,
                "partner_type": "customer",
                "is_internal_transfer": True,
                "journal_id": context["journal_id"],
                "destination_journal_id": self.destination_journal_id.id,
                "payment_method_line_id": self._get_payment_method_line(
                    payment_type
                ).id,
                "amount": payment_amount,
                "currency_id": context["currency_id"],
                "date": context["date"],
                "ref": context["ref"],
                "partner_bank_id": self.destination_journal_id.bank_account_id.id,
            }
        )
        payment_id.action_post()

        payment_line = payment_id.move_id.line_ids.filtered(
            lambda x: x.account_id.id != payment_id.destination_account_id.id
        )
        statement_line = self.env["account.bank.statement.line"].browse(
            context["active_id"]
        )
        payment_ref = "{}: {} : {}".format(
            payment_id.move_id.name, payment_line.name, context["ref"]
        )

        payment_line.write(
            {
                "name": payment_ref,
            }
        )
        statement_line.write(
            {
                "payment_ref": payment_ref,
                "payment_id": payment_id.id,
            }
        )
