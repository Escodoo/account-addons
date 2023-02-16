# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def copy_bank_accounts(self):
        oldest_company = self.search([], order="create_date").filtered(
            lambda c: c.id != self.id
        )[:1]
        if not oldest_company:
            return

        bank_accounts = self.env["res.partner.bank"].search(
            [
                ("company_id", "=", oldest_company.id),
            ]
        )

        for bank_account in bank_accounts:
            bank_account.sudo().with_context(no_sync_partner_bank=True).copy(
                default={
                    "company_id": self.id,
                }
            )

    @api.model
    def create(self, vals):
        company = super().create(vals)
        company.copy_bank_accounts()
        return company
