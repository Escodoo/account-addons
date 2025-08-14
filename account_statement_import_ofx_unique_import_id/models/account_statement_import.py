# Copyright 2025 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import uuid

from odoo import api, models


class AccountStatementImport(models.TransientModel):

    _inherit = "account.statement.import"

    @api.model
    def _prepare_ofx_transaction_line(self, transaction):
        vals = super()._prepare_ofx_transaction_line(transaction)
        vals["unique_import_id"] = str(uuid.uuid4())

        return vals
