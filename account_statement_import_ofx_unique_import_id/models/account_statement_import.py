# Copyright 2025 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountStatementImport(models.TransientModel):

    _inherit = "account.statement.import"

    @api.model
    def _prepare_ofx_transaction_line(self, transaction):
        vals = super()._prepare_ofx_transaction_line(transaction)

        transaction_date = transaction.date.strftime("%Y-%m-%d")
        unique_import_id = (
            f"{transaction_date}-{vals['payment_ref']}-{str(transaction.amount)}"
        )
        unique_import_id = (
            unique_import_id.replace(" ", "").replace(":", "-").replace(".", "")
        )

        vals["unique_import_id"] = unique_import_id

        return vals
