# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class GeneralLedgerReportWizard(models.TransientModel):

    _inherit = "general.ledger.report.wizard"

    account_type_ids = fields.Many2many(
        comodel_name="account.account.type",
        string="Account Types",
    )

    @api.onchange("account_type_ids")
    def _onchange_account_type_ids(self):
        if self.account_type_ids:
            self.account_ids = self.env["account.account"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("user_type_id", "in", self.account_type_ids.ids),
                ]
            )
        else:
            self.account_ids = None
