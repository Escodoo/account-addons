# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import models


class AccountCompensateAdvanceJournal(models.TransientModel):
    _inherit = "account.compensate.advance.journal"

    def _create_compensate_advance_account(self):
        self = self.with_context(bypass_journal_lock_date=True)
        super()._create_compensate_advance_account()
