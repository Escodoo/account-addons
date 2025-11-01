# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not self.env.context.get("no_sync_partner_bank"):
            res.sudo()._sync_partner_bank(vals)
        return res

    def write(self, vals):
        old_acc_number = self.acc_number
        old_partner_id = self.partner_id.id
        res = super().write(vals)
        if not self.env.context.get("no_sync_partner_bank"):
            self.sudo()._sync_partner_bank(vals, old_acc_number, old_partner_id)
        return res

    def unlink(self):
        if not self.env.context.get("no_sync_partner_bank_check_unlink"):
            for bank in self:
                for company in self.env["res.company"].search([]):
                    if company.id != bank.company_id.id:
                        dst_partner = company.partner_id
                        partner_bank = self.env["res.partner.bank"].search(
                            [
                                ("partner_id", "=", dst_partner.id),
                                (
                                    "sanitized_acc_number",
                                    "=",
                                    bank.sanitized_acc_number,
                                ),
                            ],
                            limit=1,
                        )
                        if partner_bank:
                            partner_bank.sudo().with_context(
                                no_sync_partner_bank_check_unlink=True
                            ).unlink()
        return super().unlink()

    def _sync_partner_bank(self, vals, old_acc_number=None, old_partner_id=None):
        for rec in self:
            for company in self.env["res.company"].search([]):
                if company.id != rec.company_id.id:
                    dst_partner = company.partner_id

                    partner_bank = self.env["res.partner.bank"].search(
                        [
                            ("partner_id", "=", dst_partner.id),
                            (
                                "sanitized_acc_number",
                                "=",
                                rec.sanitized_acc_number,
                            ),
                        ],
                        limit=1,
                    )
                    if partner_bank:
                        partner_bank.with_context(no_sync_partner_bank=True).write(vals)
                    else:
                        rec.sudo().with_context(no_sync_partner_bank=True).copy(
                            {
                                "company_id": company.id,
                                "partner_id": dst_partner.id,
                            }
                        )
