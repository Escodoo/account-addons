# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import models


class AccountInvoiceAdvanceCompensationWizard(models.TransientModel):
    _inherit = "account.invoice.advance.compensation.wizard"

    def _create_compensation_move(self):
        self = self.with_context(bypass_account_lock_to_date=True)
        return super()._create_compensation_move()
