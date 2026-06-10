# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    cr = env.cr
    cr.execute("SELECT * FROM res_partner_bank")
    res_partner_bank = cr.dictfetchall()
    if res_partner_bank:
        companies = env["res.company"].search([])
        synced_combinations = set()

        for company in companies:
            bank_accounts = company.bank_ids
            for bank_account in bank_accounts:
                for target_company in companies:
                    if target_company.id != bank_account.company_id.id:
                        dst_partner = target_company.partner_id
                        combination = (
                            bank_account.sanitized_acc_number,
                            dst_partner.id,
                            target_company.id,
                        )

                        if combination in synced_combinations:
                            continue

                        partner_bank = env["res.partner.bank"].search(
                            [
                                ("partner_id", "=", dst_partner.id),
                                ("company_id", "=", target_company.id),
                                (
                                    "sanitized_acc_number",
                                    "=",
                                    bank_account.sanitized_acc_number,
                                ),
                            ],
                            limit=1,
                        )
                        if not partner_bank:
                            try:
                                bank_account.sudo().with_context(
                                    no_sync_partner_bank=True
                                ).copy(
                                    {
                                        "company_id": target_company.id,
                                        "partner_id": dst_partner.id,
                                    }
                                )
                            except Exception as e:
                                env.cr.rollback()
                                _logger.warning(
                                    "Failed to sync bank account %s to company %s: %s",
                                    bank_account.acc_number,
                                    target_company.name,
                                    str(e),
                                )
                        synced_combinations.add(combination)
