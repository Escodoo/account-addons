# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import TransactionCase


class TestAccountCompensateAdvance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.ref("base.main_company")
        cls.partner = cls.env.ref("base.res_partner_2")
        cls.income_account = cls.env["account.account"].create(
            {
                "name": "Income Advances",
                "code": "211000ADV",
                "account_type": "asset_prepayments",
                "reconcile": True,
                "company_id": cls.company.id,
            }
        )
        cls.expense_account = cls.env["account.account"].create(
            {
                "name": "Expense Advances",
                "code": "221000ADV",
                "account_type": "asset_prepayments",
                "reconcile": True,
                "company_id": cls.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Prepayments",
                "type": "service",
                "categ_id": cls.env.ref("product.product_category_1").id,
                "property_account_income_id": cls.income_account,
                "property_account_expense_id": cls.expense_account,
            }
        )
        cls.advance_journal = cls.env["account.journal"].create(
            {
                "name": "Advance Journal",
                "code": "ADV",
                "type": "general",
                "is_advance_journal": True,
                "company_id": cls.company.id,
            }
        )

    def _create_advance_invoice(self, amount, move_type):
        invoice = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": amount,
                            "account_id": self.income_account.id
                            if move_type == "out_invoice"
                            else self.expense_account.id,
                        },
                    ),
                ],
            }
        )
        invoice.action_post()

        payment = (
            self.env["account.payment.register"]
            .with_context(
                active_model="account.move",
                active_ids=invoice.ids,
            )
            .create(
                {
                    "payment_date": fields.Date.today(),
                    "journal_id": self.env["account.journal"]
                    .search([("type", "=", "bank")], limit=1)
                    .id,
                    "amount": amount,
                }
            )
        )
        payment._create_payments()
        return invoice

    def _create_customer_invoice(self, amount):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": amount,
                            "account_id": self.income_account.id,
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def _create_supplier_invoice(self, amount):
        invoice = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": amount,
                            "account_id": self.expense_account.id,
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def test_01_customer_invoice_compensation(self):
        """Test customer invoice advance compensation"""
        advance_invoice = self._create_advance_invoice(500, "out_invoice")
        invoice = self._create_customer_invoice(1000)

        advance_line = advance_invoice.line_ids.filtered(
            lambda l: l.account_id == self.income_account
        )
        invoice_line = invoice.line_ids.filtered(
            lambda l: l.account_id.account_type == "asset_receivable"
        )

        wizard = (
            self.env["account.compensate.advance.journal"]
            .with_context(
                active_model="account.move",
                active_ids=[invoice.id],
                default_move_type="out_invoice",
            )
            .create(
                {
                    "advance_id": advance_line.id,
                    "line_id": invoice_line.id,
                    "journal_id": self.advance_journal.id,
                    "amount": 300.00,
                    "date": fields.Date.today(),
                }
            )
        )

        self.assertEqual(wizard.advance_balance, 500.00)
        self.assertEqual(wizard.currency_id, self.company.currency_id)

        wizard.action_compensate_advance_account()
        residual = advance_line.amount_residual

        self.assertEqual(residual, -200.00)

        matched_amounts = [
            p.amount
            for p in (advance_line.matched_debit_ids | advance_line.matched_credit_ids)
        ]
        self.assertIn(300.00, matched_amounts)

    def test_02_supplier_invoice_compensation(self):
        """Test supplier invoice advance compensation"""
        advance_invoice = self._create_advance_invoice(600, "in_invoice")
        invoice = self._create_supplier_invoice(800)

        advance_line = advance_invoice.line_ids.filtered(
            lambda l: l.account_id == self.expense_account
        )
        invoice_line = invoice.line_ids.filtered(
            lambda l: l.account_id.account_type == "liability_payable"
        )

        wizard = (
            self.env["account.compensate.advance.journal"]
            .with_context(
                active_model="account.move",
                active_ids=[invoice.id],
                default_move_type="in_invoice",
            )
            .create(
                {
                    "advance_id": advance_line.id,
                    "line_id": invoice_line.id,
                    "journal_id": self.advance_journal.id,
                    "amount": 400.00,
                    "date": fields.Date.today(),
                }
            )
        )

        self.assertEqual(wizard.advance_balance, 600.00)
        self.assertEqual(wizard.currency_id, self.company.currency_id)

        wizard.action_compensate_advance_account()
        residual = advance_line.amount_residual

        self.assertEqual(residual, 200.00)

        matched_amounts = [
            p.amount
            for p in (advance_line.matched_debit_ids | advance_line.matched_credit_ids)
        ]
        self.assertIn(400.00, matched_amounts)
