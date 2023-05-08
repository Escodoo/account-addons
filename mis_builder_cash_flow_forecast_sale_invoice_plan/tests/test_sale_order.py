# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleOrder(TransactionCase):
    def setUp(self):
        super(TestSaleOrder, self).setUp()
        self.currency_eur = self.env.ref("base.EUR")
        self.currency_usd = self.env.ref("base.USD")
        self.product = self.env["product.product"].create(
            {"name": "Test Product", "list_price": 100}
        )
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                "company_id": self.env.ref("base.main_company").id,
                "payment_term_id": self.env.ref(
                    "account.account_payment_term_immediate"
                ).id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": self.product.list_price,
                        },
                    ),
                ],
            }
        )

    def test_compute_payment_terms(self):
        expected_values = [(fields.Date.today().strftime("%Y-%m-%d"), 115.0, 115.0)]
        values = self.sale_order._compute_payment_terms(
            date=self.sale_order.date_order,
            total_balance=self.sale_order.amount_total,
            total_amount_currency=self.sale_order.amount_total,
        )
        self.assertEqual(values, expected_values)

        self.env["sale.invoice.plan"].create(
            {
                "sale_id": self.sale_order.id,
                "partner_id": self.env.ref("base.res_partner_2").id,
                "plan_date": fields.Date.today(),
            }
        )
        self.assertTrue(self.sale_order.invoice_plan_ids)

        values = []
        invoice_plan = self.env["sale.invoice.plan"].search(
            [("sale_id", "=", self.sale_order.id)]
        )
        self.assertFalse(invoice_plan.invoiced)

        total_amount_currency = self.sale_order.amount_total * (
            invoice_plan.percent / 100
        )
        self.assertEqual(total_amount_currency, 0.0)

        self.sale_order.currency_id = self.currency_eur
        self.assertTrue(
            self.sale_order.currency_id
            and self.sale_order.company_id
            and self.sale_order.currency_id != self.sale_order.company_id.currency_id
        )
        cur = self.sale_order.currency_id
        total_amount_currency = cur.round(total_amount_currency)

        date = invoice_plan.plan_date
        total_amount_currency = total_amount_currency
        total_balance = self.sale_order._compute_amount_uninvoiced_company_currency(
            total_amount_currency
        )
        self.assertEqual(total_balance, 0.00)

        values = self.sale_order._compute_payment_terms(
            date=date,
            total_balance=total_balance,
            total_amount_currency=total_amount_currency,
        )
        expected_values = [[fields.Date.today().strftime("%Y-%m-%d"), 0.0, 0.0]]
        self.assertEqual(values, expected_values)
