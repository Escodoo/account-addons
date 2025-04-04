# Copyright 2025 - TODAY, Caroline Azevedo <caroline.azevedo@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _prepare_other_payment_values(self):
        values = super()._prepare_other_payment_values()

        bill = self.env["account.move"].search(
            [("ref", "=", self.ref), ("move_type", "=", "in_invoice")], limit=1
        )

        ref = f"{self.ref} | {self.partner_id.name} | {self.company_id.name}"
        if bill:
            ref = f"{bill.name} | {ref}"
        values["ref"] = ref

        return values
