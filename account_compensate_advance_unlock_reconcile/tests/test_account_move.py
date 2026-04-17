# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestAccountMoveLockToDate(TransactionCase):
    """Tests for AccountMove._check_lock_to_dates override.

    The module overrides _check_lock_to_dates to allow bypassing the lock
    when the context key 'bypass_account_lock_to_date' is set to True.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)], limit=1
        )
        cls.account = cls.env["account.account"].search(
            [
                ("company_ids", "in", cls.company.id),
                ("account_type", "not in", ["asset_receivable", "liability_payable"]),
            ],
            limit=1,
        )

    def _create_move(self):
        """Helper: create a minimal posted journal entry."""
        move = self.env["account.move"].create(
            {
                "journal_id": self.journal.id,
                "move_type": "entry",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.account.id,
                            "debit": 100.0,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.account.id,
                            "debit": 0.0,
                            "credit": 100.0,
                        },
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def test_check_lock_to_dates_bypass_skips_super(self):
        """When bypass_account_lock_to_date is True, super() must NOT be called."""
        move = self._create_move()
        parent_method = (
            "odoo.addons.account_lock_to_date.models.account_move"
            ".AccountMove._check_lock_to_dates"
        )
        with patch(parent_method) as mock_super:
            move.with_context(bypass_account_lock_to_date=True)._check_lock_to_dates()
            mock_super.assert_not_called()

    def test_check_lock_to_dates_no_bypass_calls_super(self):
        """When bypass_account_lock_to_date is absent/False, super() must be called."""
        move = self._create_move()
        parent_method = (
            "odoo.addons.account_lock_to_date.models.account_move"
            ".AccountMove._check_lock_to_dates"
        )
        with patch(parent_method) as mock_super:
            move._check_lock_to_dates()
            mock_super.assert_called_once()

    def test_check_lock_to_dates_bypass_false_calls_super(self):
        """Explicit False for bypass_account_lock_to_date still calls super()."""
        move = self._create_move()
        parent_method = (
            "odoo.addons.account_lock_to_date.models.account_move"
            ".AccountMove._check_lock_to_dates"
        )
        with patch(parent_method) as mock_super:
            move.with_context(bypass_account_lock_to_date=False)._check_lock_to_dates()
            mock_super.assert_called_once()
