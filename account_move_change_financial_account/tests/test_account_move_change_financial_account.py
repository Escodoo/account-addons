# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountAccountFinancialRules(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref=chart_template_ref)
        cls.account_move = cls.env["account.move"]
        cls.account_move_line = cls.env["account.move.line"]
        cls.financial_rules = cls.env["account.account.financial.rules"]

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        cls.receivable_account = cls.env["account.account"].search(
            [("internal_type", "=", "receivable")], limit=1
        )
        cls.revenue_account = cls.env["account.account"].create(
            {
                "name": "Test Revenue Account",
                "code": "TRA",
                "user_type_id": cls.env.ref("account.data_account_type_revenue").id,
            }
        )
        cls.new_receivable_account = cls.env["account.account"].create(
            {
                "name": "New Receivable Account",
                "code": "NEWRCV",
                "user_type_id": cls.env.ref("account.data_account_type_receivable").id,
                "reconcile": True,
            }
        )

    def test_financial_rules_creation(self):
        rule = self.financial_rules.create(
            {
                "name": "Test Rule",
                "domain": "[('partner_id', '=', %s)]" % self.partner.id,
                "financial_account_id": self.new_receivable_account.id,
            }
        )
        self.assertTrue(rule)

    def test_account_move_line_creation(self):
        self.financial_rules.create(
            {
                "name": "Test Rule",
                "domain": "[('partner_id', '=', %s)]" % self.partner.id,
                "financial_account_id": self.new_receivable_account.id,
            }
        )

        # Test a rule that will not be applied to any line
        self.financial_rules.create(
            {
                "name": "Test Rule No Match",
                "domain": "[('partner_id', '=', -1)]",
                "financial_account_id": self.new_receivable_account.id,
            }
        )

        move = self.account_move.create(
            {
                "partner_id": self.partner.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.receivable_account.id,
                            "partner_id": self.partner.id,
                            "name": "Receivable line",
                            "debit": 100.0,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.revenue_account.id,
                            "partner_id": self.partner.id,
                            "name": "Revenue line",
                            "debit": 0.0,
                            "credit": 100.0,
                        },
                    ),
                ],
            }
        )

        receivable_line = move.line_ids.filtered(
            lambda line: line.account_id == self.receivable_account
        )
        self.assertFalse(receivable_line)

        new_receivable_line = move.line_ids.filtered(
            lambda line: line.account_id == self.new_receivable_account
        )
        self.assertTrue(new_receivable_line)

    def test_lines_to_change_no_match(self):
        # Test a rule that will not be applied to any line
        self.financial_rules.create(
            {
                "name": "Test Rule No Match",
                "domain": "[('partner_id', '=', -1)]",
                "financial_account_id": self.new_receivable_account.id,
            }
        )

        move = self.account_move.create(
            {
                "partner_id": self.partner.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.receivable_account.id,
                            "partner_id": self.partner.id,
                            "name": "Receivable line",
                            "debit": 100.0,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.revenue_account.id,
                            "partner_id": self.partner.id,
                            "name": "Revenue line",
                            "debit": 0.0,
                            "credit": 100.0,
                        },
                    ),
                ],
            }
        )

        # Check if the original receivable account is still used when there's no matching rule
        receivable_line = move.line_ids.filtered(
            lambda line: line.account_id == self.receivable_account
        )
        self.assertTrue(receivable_line)

        # Check if the new_receivable_account is not used when there's no matching rule
        new_receivable_line = move.line_ids.filtered(
            lambda line: line.account_id == self.new_receivable_account
        )
        self.assertFalse(new_receivable_line)

    def test_no_matching_financial_lines(self):
        # Test that the code doesn't enter the for loop when there are no financial lines

        move = self.account_move.create(
            {
                "partner_id": self.partner.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.revenue_account.id,
                            "partner_id": self.partner.id,
                            "name": "Revenue line",
                            "debit": 0.0,
                            "credit": 100.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": self.revenue_account.id,
                            "partner_id": self.partner.id,
                            "name": "Revenue line 2",
                            "debit": 100.0,
                            "credit": 0.0,
                        },
                    ),
                ],
            }
        )

        # Check if the new_receivable_account is not used when there are no financial lines
        new_receivable_line = move.line_ids.filtered(
            lambda line: line.account_id == self.new_receivable_account
        )
        self.assertFalse(new_receivable_line)
