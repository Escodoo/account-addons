# Copyright 2025 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class InternalTransferWizard(models.TransientModel):
    _name = "internal.transfer.wizard"
    _description = "Internal Transfer Wizard"

    def _get_destination_journal_domain(self):
        journal_id = self.env.context.get("journal_id")
        return [("type", "in", ("bank", "cash")), ("id", "!=", journal_id)]

    destination_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Destination Journal",
        domain=_get_destination_journal_domain,
    )
    payment_method_id = fields.Many2one(
        comodel_name="account.payment.method",
        string="Payment Method",
        domain=[("code", "not in", ("240", "400", "500"))],
    )

    def action_create_internal_transfer(self):
        context = self.env.context

        payment_type = "inbound"
        payment_amount = context["amount"]
        if payment_amount < 0.0:
            payment_type = "outbound"
            payment_amount = context["amount"] * -1

        payment_id = self.env["account.payment"].create(
            {
                "name": "/",
                "company_id": context["company_id"],
                "payment_type": payment_type,
                "partner_type": "customer",
                "is_internal_transfer": True,
                "journal_id": context["journal_id"],
                "destination_journal_id": self.destination_journal_id.id,
                "payment_method_id": self.payment_method_id.id,
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

        statement_line.write(
            {
                "payment_ref": "{}: {} : {}".format(
                    payment_id.move_id.name, payment_line.name, context["ref"]
                ),
                "payment_id": payment_id.id,
            }
        )
