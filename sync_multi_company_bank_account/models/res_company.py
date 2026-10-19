# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
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
            dst_partner = self.partner_id
            existing = self.env["res.partner.bank"].search(
                [
                    ("partner_id", "=", dst_partner.id),
                    ("sanitized_acc_number", "=", bank_account.sanitized_acc_number),
                ],
                limit=1,
            )
            if not existing:
                bank_account.sudo().with_context(no_sync_partner_bank=True).copy(
                    default={
                        "company_id": self.id,
                        "partner_id": dst_partner.id,
                    }
                )

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        for company in companies:
            company.copy_bank_accounts()
        return companies
