# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestJournalDashboardBankAccountBalance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.default_account = cls.env["account.account"].search(
            [
                ("company_ids", "in", cls.company.id),
                ("account_type", "=", "asset_cash"),
                ("deprecated", "=", False),
            ],
            limit=1,
        )
        if not cls.default_account:
            cls.default_account = cls.env["account.account"].search(
                [
                    ("company_ids", "in", cls.company.id),
                    ("account_type", "=", "asset_current"),
                    ("deprecated", "=", False),
                ],
                limit=1,
            )

        cls.bank_journal = cls.env["account.journal"].create(
            {
                "name": "Test Bank Dashboard",
                "code": "TBD",
                "type": "bank",
                "company_id": cls.company.id,
                "default_account_id": cls.default_account.id,
            }
        )
        cls.sale_journal = cls.env["account.journal"].create(
            {
                "name": "Test Sale Dashboard",
                "code": "TSD",
                "type": "sale",
                "company_id": cls.company.id,
            }
        )

    def _new_dashboard_data(self):
        return {
            self.bank_journal.id: {},
            self.sale_journal.id: {},
        }

    def test_fill_bank_cash_dashboard_data_adds_custom_balance_fields(self):
        dashboard_data = self._new_dashboard_data()

        (self.bank_journal | self.sale_journal)._fill_bank_cash_dashboard_data(
            dashboard_data
        )

        expected_balance, _nb_lines = (
            self.bank_journal._get_journal_bank_account_balance(
                domain=[("parent_state", "=", "posted")]
            )
        )

        self.assertIn("bank_account_balance", dashboard_data[self.bank_journal.id])
        self.assertIn(
            "formatted_bank_account_balance", dashboard_data[self.bank_journal.id]
        )
        self.assertEqual(
            dashboard_data[self.bank_journal.id]["bank_account_balance"],
            expected_balance,
        )
        self.assertTrue(
            dashboard_data[self.bank_journal.id]["formatted_bank_account_balance"]
        )

    def test_fill_bank_cash_dashboard_data_does_not_add_fields_for_non_bank_journal(
        self,
    ):
        dashboard_data = self._new_dashboard_data()

        (self.bank_journal | self.sale_journal)._fill_bank_cash_dashboard_data(
            dashboard_data
        )

        self.assertNotIn("bank_account_balance", dashboard_data[self.sale_journal.id])
        self.assertNotIn(
            "formatted_bank_account_balance", dashboard_data[self.sale_journal.id]
        )
