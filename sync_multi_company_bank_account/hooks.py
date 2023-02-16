# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("SELECT * FROM res_partner_bank")
    res_partner_bank = []
    res_partner_bank = cr.dictfetchall()
    if res_partner_bank:
        bank_accounts = env["res.partner.bank"]
        companies = env["res.company"].search([])
        for company in companies:
            bank_accounts |= company.bank_ids
        for bank_account in bank_accounts:
            for company in companies:
                if company.id != bank_account.company_id.id:
                    if bank_account.acc_number not in company.bank_ids.mapped(
                        "acc_number"
                    ):
                        bank_account.sudo().with_context(
                            no_sync_partner_bank=True
                        ).copy({"company_id": company.id})
