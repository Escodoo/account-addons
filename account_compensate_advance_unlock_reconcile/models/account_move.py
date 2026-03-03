# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_lock_to_dates(self):
        """
        Prevent moves that are on or after the lock to date, unless the context
        allows bypass.
        """
        # Check if the context allows bypassing the lock to date
        if self.env.context.get("bypass_account_lock_to_date"):
            return

        # Call the parent method to enforce lock checks if no bypass
        return super()._check_lock_to_dates()
