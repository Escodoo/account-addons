# Copyright 2025 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools.misc import formatLang


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _fill_bank_cash_dashboard_data(self, dashboard_data):
        bank_cash_journals = self.filtered(
            lambda journal: journal.type in ("bank", "cash")
        )
        if not bank_cash_journals:
            return

        super()._fill_bank_cash_dashboard_data(dashboard_data)

        for journal in bank_cash_journals:
            currency = journal.currency_id or journal.company_id.currency_id
            bank_account_balance, nb_lines = journal._get_journal_bank_account_balance(
                domain=[("parent_state", "=", "posted")]
            )
            dashboard_data[journal.id].update(
                {
                    "bank_account_balance": bank_account_balance,
                    "formatted_bank_account_balance": formatLang(
                        self.env,
                        currency.round(bank_account_balance),
                        currency_obj=currency,
                    ),
                }
            )
