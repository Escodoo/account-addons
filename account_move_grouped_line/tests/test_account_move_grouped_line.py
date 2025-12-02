# Copyright 2025 Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMoveGroupedLine(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.account_revenue = cls.company_data["default_account_revenue"]
        cls.account_expense = cls.company_data["default_account_expense"]
        cls.account_receivable = cls.company_data["default_account_receivable"]

        # Create a journal entry with multiple lines using the same accounts
        cls.test_move = cls.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2025-01-01"),
                "line_ids": [
                    (
                        0,
                        None,
                        {
                            "name": "revenue line 1",
                            "account_id": cls.account_revenue.id,
                            "debit": 500.0,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        None,
                        {
                            "name": "revenue line 2",
                            "account_id": cls.account_revenue.id,
                            "debit": 300.0,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        None,
                        {
                            "name": "expense line 1",
                            "account_id": cls.account_expense.id,
                            "debit": 200.0,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        None,
                        {
                            "name": "counterpart line",
                            "account_id": cls.account_receivable.id,
                            "debit": 0.0,
                            "credit": 1000.0,
                        },
                    ),
                ],
            }
        )

    def test_grouped_items_computed(self):
        """Test that grouped_items_id field is computed correctly."""
        self.assertTrue(self.test_move.grouped_items_id)
        # Should have 3 grouped lines (revenue, expense, receivable)
        self.assertEqual(len(self.test_move.grouped_items_id), 3)

    def test_grouped_items_debit_sum(self):
        """Test that debit values are correctly summed by account."""
        grouped_lines = self.test_move.grouped_items_id

        # Find the grouped line for revenue account
        revenue_grouped = grouped_lines.filtered(
            lambda rec: rec.account_id == self.account_revenue
        )
        self.assertEqual(len(revenue_grouped), 1)
        # Revenue: 500 + 300 = 800
        self.assertEqual(revenue_grouped.debit, 800.0)
        self.assertEqual(revenue_grouped.credit, 0.0)

    def test_grouped_items_credit_sum(self):
        """Test that credit values are correctly summed by account."""
        grouped_lines = self.test_move.grouped_items_id

        # Find the grouped line for receivable account
        receivable_grouped = grouped_lines.filtered(
            lambda rec: rec.account_id == self.account_receivable
        )
        self.assertEqual(len(receivable_grouped), 1)
        # Receivable: 1000 credit
        self.assertEqual(receivable_grouped.debit, 0.0)
        self.assertEqual(receivable_grouped.credit, 1000.0)

    def test_grouped_items_expense(self):
        """Test that expense account is grouped correctly."""
        grouped_lines = self.test_move.grouped_items_id

        # Find the grouped line for expense account
        expense_grouped = grouped_lines.filtered(
            lambda rec: rec.account_id == self.account_expense
        )
        self.assertEqual(len(expense_grouped), 1)
        # Expense: 200
        self.assertEqual(expense_grouped.debit, 200.0)
        self.assertEqual(expense_grouped.credit, 0.0)

    def test_grouped_items_balance(self):
        """Test that total debit equals total credit in grouped lines."""
        grouped_lines = self.test_move.grouped_items_id

        total_debit = sum(grouped_lines.mapped("debit"))
        total_credit = sum(grouped_lines.mapped("credit"))

        self.assertEqual(total_debit, total_credit)
        self.assertEqual(total_debit, 1000.0)

    def test_grouped_items_account_name(self):
        """Test that name field is related to account name."""
        grouped_lines = self.test_move.grouped_items_id

        for line in grouped_lines:
            self.assertEqual(line.name, line.account_id.name)

    def test_grouped_items_currency(self):
        """Test that currency_id is set correctly."""
        grouped_lines = self.test_move.grouped_items_id
        company_currency = self.env.company.currency_id

        for line in grouped_lines:
            self.assertEqual(line.currency_id, company_currency)

    def test_empty_move(self):
        """Test grouped items for a move without lines."""
        empty_move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": fields.Date.from_string("2025-01-01"),
            }
        )
        self.assertFalse(empty_move.grouped_items_id)

    def test_grouped_items_multiple_lines_same_account(self):
        """Test that multiple lines with same account are grouped correctly.

        This test uses self.test_move which has:
        - 2 revenue lines (500 + 300 = 800 debit)
        - 1 expense line (200 debit)
        - 1 receivable line (1000 credit)
        """
        grouped_lines = self.test_move.grouped_items_id

        # Should have 3 grouped lines (revenue, expense, receivable)
        self.assertEqual(len(grouped_lines), 3)

        # Revenue account has 2 lines that should be summed
        revenue_grouped = grouped_lines.filtered(
            lambda rec: rec.account_id == self.account_revenue
        )
        self.assertEqual(len(revenue_grouped), 1)
        self.assertEqual(revenue_grouped.debit, 800.0)  # 500 + 300

        # Expense account has 1 line
        expense_grouped = grouped_lines.filtered(
            lambda rec: rec.account_id == self.account_expense
        )
        self.assertEqual(len(expense_grouped), 1)
        self.assertEqual(expense_grouped.debit, 200.0)

        # Receivable account has 1 line with credit
        receivable_grouped = grouped_lines.filtered(
            lambda rec: rec.account_id == self.account_receivable
        )
        self.assertEqual(len(receivable_grouped), 1)
        self.assertEqual(receivable_grouped.credit, 1000.0)
