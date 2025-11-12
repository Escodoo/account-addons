# Copyright 2025 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import TransactionCase


class TestInternalTransferWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.currency = cls.company.currency_id
        cls.suspense_account = cls.env["account.account"].search(
            [("account_type", "=", "asset_current")], limit=1
        )
        cls.bank_journal_1 = cls.env["account.journal"].create(
            {
                "name": "Bank 1",
                "code": "B1",
                "type": "bank",
                "company_id": cls.company.id,
                "suspense_account_id": cls.suspense_account.id,
            }
        )
        cls.bank_journal_2 = cls.env["account.journal"].create(
            {
                "name": "Bank 2",
                "code": "B2",
                "type": "bank",
                "company_id": cls.company.id,
                "suspense_account_id": cls.suspense_account.id,
            }
        )
        cls.bank_account = cls.env["res.partner.bank"].create(
            {
                "acc_number": "123456",
                "partner_id": cls.company.partner_id.id,
            }
        )
        cls.bank_journal_2.bank_account_id = cls.bank_account.id
        cls.payment_method = cls.env["account.payment.method"].search(
            [("payment_type", "=", "inbound")], limit=1
        )
        cls.statement = cls.env["account.bank.statement"].create(
            {
                "name": "Test Statement",
                "journal_id": cls.bank_journal_1.id,
                "company_id": cls.company.id,
                "date": fields.Date.today(),
            }
        )
        cls.statement_line = cls.env["account.bank.statement.line"].create(
            {
                "journal_id": cls.bank_journal_1.id,
                "statement_id": cls.statement.id,
                "amount": 100.0,
                "payment_ref": "Initial Ref",
                "date": fields.Date.today(),
            }
        )

    def test_internal_transfer_inbound(self):
        wizard = (
            self.env["internal.transfer.wizard"]
            .with_context(
                journal_id=self.bank_journal_1.id,
                amount=100.0,
                company_id=self.company.id,
                currency_id=self.currency.id,
                date=fields.Date.today(),
                ref="Inbound Transfer",
                active_id=self.statement_line.id,
            )
            .create(
                {
                    "destination_journal_id": self.bank_journal_2.id,
                    "payment_method_id": self.payment_method.id,
                }
            )
        )

        wizard.action_create_internal_transfer()

        payment = self.statement_line.payment_id
        self.assertTrue(payment)
        self.assertEqual(payment.payment_type, "inbound")
        self.assertTrue(payment.is_internal_transfer)
        self.assertEqual(payment.state, "posted")

        payment_line = payment.move_id.line_ids.filtered(
            lambda x: x.account_id != payment.destination_account_id
        )
        self.assertEqual(len(payment_line), 1)

        self.assertEqual(payment_line.name, self.statement_line.payment_ref)
        self.assertIn("Inbound Transfer", payment_line.name)

    def test_internal_transfer_outbound(self):
        wizard = (
            self.env["internal.transfer.wizard"]
            .with_context(
                journal_id=self.bank_journal_1.id,
                amount=-150.0,
                company_id=self.company.id,
                currency_id=self.currency.id,
                date=fields.Date.today(),
                ref="Outbound Transfer",
                active_id=self.statement_line.id,
            )
            .create(
                {
                    "destination_journal_id": self.bank_journal_2.id,
                    "payment_method_id": self.payment_method.id,
                }
            )
        )

        wizard.action_create_internal_transfer()

        payment = self.statement_line.payment_id
        self.assertTrue(payment)
        self.assertEqual(payment.payment_type, "outbound")
        self.assertEqual(payment.amount, 150.0)
        self.assertEqual(payment.state, "posted")

        payment_line = payment.move_id.line_ids.filtered(
            lambda x: x.account_id != payment.destination_account_id
        )
        self.assertEqual(len(payment_line), 1)

        self.assertEqual(payment_line.name, self.statement_line.payment_ref)
        self.assertIn("Outbound Transfer", payment_line.name)
