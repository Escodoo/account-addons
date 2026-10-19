# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountPaymentRegisterInstallment(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice = cls._create_invoice_one_line(
            price_unit=300.0,
            tax_ids=cls.env["account.tax"],
            post=True,
        )

    def test_create_payments_without_installment_mode(self):
        payments = self._register_payment(
            self.invoice,
            amount=300.0,
            payment_date=date(2026, 1, 15),
            installment_mode=False,
            installment_quantity=3,
        )

        self.assertEqual(len(payments), 1)

    def test_create_payments_with_quantity_one(self):
        payments = self._register_payment(
            self.invoice,
            amount=300.0,
            payment_date=date(2026, 1, 15),
            installment_mode=True,
            installment_quantity=1,
        )

        self.assertEqual(len(payments), 1)

    def test_create_payments_with_installments(self):
        payment_date = date(2026, 1, 15)
        installment_quantity = 3

        payments = self._register_payment(
            self.invoice,
            amount=300.0,
            payment_date=payment_date,
            installment_mode=True,
            installment_quantity=installment_quantity,
        )

        self.assertEqual(len(payments), installment_quantity)

        payments_by_date = payments.sorted(lambda payment: payment.date)
        expected_dates = [
            payment_date + relativedelta(months=1),
            payment_date + relativedelta(months=2),
            payment_date + relativedelta(months=3),
        ]
        self.assertEqual(payments_by_date.mapped("date"), expected_dates)

        for payment in payments_by_date:
            self.assertAlmostEqual(payment.amount, 100.0, places=2)
