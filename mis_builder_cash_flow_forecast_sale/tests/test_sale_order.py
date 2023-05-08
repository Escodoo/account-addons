# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


import datetime

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleOrder(TransactionCase):
    def setUp(self):
        super(TestSaleOrder, self).setUp()
        self.currency_eur = self.env.ref("base.EUR")
        self.currency_usd = self.env.ref("base.USD")
        self.company = self.env["res.company"].create({"name": "Test Company"})
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.payment_term = self.env["account.payment.term"].create(
            {
                "name": "30 Days",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "balance",
                            "days": 30,
                        },
                    )
                ],
            }
        )
        self.product = self.env["product.product"].create(
            {"name": "Test Product", "list_price": 100}
        )
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "price_unit": 100,
                            "product_uom_qty": 2,
                        },
                    )
                ],
            }
        )
        self.account_move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "date": "2019-01-01",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "invoice_line",
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                        },
                    ),
                ],
            }
        )
        self.account = self.env["account.account"].create(
            {
                "name": "TAX_WAIT",
                "code": "TWAIT",
                "user_type_id": self.env.ref(
                    "account.data_account_type_current_liabilities"
                ).id,
                "reconcile": True,
                "company_id": self.company.id,
            }
        )

        self.forecast_line1 = self.env["mis.cash_flow.forecast_line"].create(
            {
                "account_id": self.account.id,
                "balance": 200,
                "company_id": self.company.id,
                "date": fields.Date.today(),
                "name": "Forecast Line 1",
                "res_model": "sale.order",
                "res_id": self.sale_order.id,
            }
        )
        self.forecast_line2 = self.env["mis.cash_flow.forecast_line"].create(
            {
                "account_id": self.account.id,
                "balance": 200,
                "company_id": self.company.id,
                "date": fields.Date.today(),
                "name": "Forecast Line 2",
                "res_model": "sale.order",
                "res_id": self.sale_order.id,
            }
        )

    def test_compute_forecast_uninvoiced_amount(self):
        self.sale_order.invoice_ids.unlink()
        self.sale_order._compute_forecast_uninvoiced_amount()
        self.assertEqual(self.sale_order.forecast_uninvoiced_amount, 200)

        self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": self.product.name,
                            "quantity": 1,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )

        self.sale_order._compute_forecast_uninvoiced_amount()
        self.assertEqual(self.sale_order.forecast_uninvoiced_amount, 200)

        invoice = self.env["account.move"].search([("state", "=", "draft")], limit=1)
        invoice.action_post()
        self.sale_order._compute_forecast_uninvoiced_amount()
        self.assertEqual(self.sale_order.forecast_uninvoiced_amount, 200)

        self.sale_order.action_cancel()
        self.sale_order._compute_forecast_uninvoiced_amount()
        self.assertEqual(self.sale_order.forecast_uninvoiced_amount, 0)

        self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": self.product.name,
                            "quantity": 1,
                            "price_unit": self.product.list_price,
                        },
                    )
                ],
            }
        )
        self.sale_order._compute_forecast_uninvoiced_amount()
        self.sale_order.write({"amount_total": 50})

    def test_compute_mis_cash_flow_forecast_line_ids(self):
        self.sale_order.write(
            {
                "mis_cash_flow_forecast_line_ids": [
                    (6, 0, [self.forecast_line1.id, self.forecast_line2.id])
                ]
            }
        )
        self.assertEqual(len(self.sale_order.mis_cash_flow_forecast_line_ids), 2)
        self.assertIn(
            self.forecast_line1, self.sale_order.mis_cash_flow_forecast_line_ids
        )
        self.assertIn(
            self.forecast_line2, self.sale_order.mis_cash_flow_forecast_line_ids
        )

    def test_compute_amount_uninvoiced_company_currency(self):
        self.sale_order.currency_id = self.currency_eur
        self.assertTrue(
            self.sale_order.currency_id
            and self.sale_order.company_id
            and self.sale_order.currency_id != self.sale_order.company_id.currency_id
        )
        cur = self.sale_order.currency_id
        amount_uninvoiced = 100.0
        price_subtotal = cur.round(amount_uninvoiced)
        amount_uninvoiced = cur._convert(
            price_subtotal,
            self.sale_order.company_id.currency_id,
            self.sale_order.company_id,
            fields.Date.today(),
        )
        result = self.sale_order._compute_amount_uninvoiced_company_currency(
            amount_uninvoiced
        )
        self.assertEqual(result, amount_uninvoiced)
        amount_uninvoiced = 100.0
        result = self.sale_order._compute_amount_uninvoiced_company_currency(
            amount_uninvoiced
        )
        self.assertEqual(result, amount_uninvoiced)

    def test_get_mis_cash_flow_forecast_update_trigger_fields(self):
        expected_fields = [
            "partner_id",
            "pricelist_id",
            "fiscal_position_id",
            "currency_id",
            "order_line",
            "payment_term_id",
            "currency_rate",
            "invoice_status",
            "state",
            "invoice_ids",
            "invoice_count",
        ]
        result_fields = (
            self.sale_order._get_mis_cash_flow_forecast_update_trigger_fields()
        )
        self.assertEqual(expected_fields, result_fields)

    def test_write(self):
        res = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "price_unit": 100,
                            "product_uom_qty": 2,
                        },
                    )
                ],
            }
        )
        res.write(
            {
                "currency_id": self.currency_usd.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "price_unit": 75,
                            "product_uom_qty": 2,
                        },
                    )
                ],
            }
        )
        res.company_id.enable_sale_mis_cash_flow_forecast = True
        res.state = "sale"
        self.assertTrue(
            res.state in ["sale", "done", "cancel"]
            and res.company_id.enable_sale_mis_cash_flow_forecast
        )
        res.with_delay()._generate_mis_cash_flow_forecast_lines()

    def test_unlink(self):
        self.sale_order.write(
            {
                "mis_cash_flow_forecast_line_ids": [
                    (6, 0, [self.forecast_line1.id, self.forecast_line2.id])
                ]
            }
        )
        self.assertTrue(self.sale_order.mis_cash_flow_forecast_line_ids)
        self.sale_order.unlink()
        self.assertFalse(self.sale_order.mis_cash_flow_forecast_line_ids)

    def test_prepare_mis_cash_flow_forecast_line(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_1").id,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        payment_term_item = "30"
        payment_term_count = 1
        date = fields.Date.today()
        amount = 100.00

        result = sale_order._prepare_mis_cash_flow_forecast_line(
            payment_term_item, payment_term_count, date, amount
        )

        expected_result = {
            "name": f"{sale_order.display_name} - {payment_term_item}/{payment_term_count}",
            "date": date,
            "account_id": sale_order.partner_id.property_account_receivable_id.id,
            "partner_id": sale_order.partner_id.id,
            "balance": amount,
            "company_id": sale_order.company_id.id,
            "res_model_id": self.env.ref("sale.model_sale_order").id,
            "res_id": sale_order.id,
            "parent_res_model_id": self.env.ref("sale.model_sale_order").id,
            "parent_res_id": sale_order.id,
        }

        self.assertDictEqual(result, expected_result)

    def test_action_show_mis_forecast(self):
        self.sale_order.write(
            {
                "mis_cash_flow_forecast_line_ids": [
                    (
                        6,
                        0,
                        [
                            self.forecast_line1.id,
                            self.forecast_line2.id,
                        ],
                    )
                ]
            }
        )
        action = self.sale_order.action_show_mis_forecast()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["name"], "Cash Flow Forecast - Sale")
        self.assertEqual(action["res_model"], "mis.cash_flow.forecast_line")
        self.assertEqual(
            action["domain"],
            [
                ("parent_res_model", "=", "sale.order"),
                ("parent_res_id", "=", self.sale_order.id),
            ],
        )
        self.assertIn("pivot", action["view_mode"])
        self.assertIn("tree", action["view_mode"])
        self.assertNotIn("group_by", action["context"])

    def test_compute_payment_terms_no_payment_term(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                "company_id": self.env.ref("base.main_company").id,
                "currency_id": self.env.ref("base.USD").id,
            }
        )
        date = fields.Date.today()
        total_balance = 100.0
        total_amount_currency = 100.0

        self.assertFalse(sale_order.payment_term_id)
        payment_terms = sale_order._compute_payment_terms(
            date, total_balance, total_amount_currency
        )

        self.assertEqual(len(payment_terms), 1)
        self.assertEqual(payment_terms[0][0], fields.Date.to_string(date))
        self.assertEqual(payment_terms[0][1], total_balance)
        self.assertEqual(payment_terms[0][2], total_amount_currency)

    def test_compute_payment_terms_multi_currencies(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                "company_id": self.env.ref("base.main_company").id,
                "payment_term_id": self.env.ref(
                    "account.account_payment_term_immediate"
                ).id,
            }
        )
        date = fields.Date.today()
        total_balance = 100.0
        total_amount_currency = 90.0
        sale_order.currency_id = self.currency_eur

        self.assertTrue(sale_order.payment_term_id)
        payment_terms = sale_order._compute_payment_terms(
            date, total_balance, total_amount_currency
        )
        self.assertFalse(sale_order.currency_id == sale_order.company_id.currency_id)
        self.assertEqual(len(payment_terms), 1)
        self.assertEqual(payment_terms[0][0], fields.Date.to_string(date))
        self.assertEqual(payment_terms[0][1], total_balance)
        self.assertEqual(payment_terms[0][2], 90.0)

    def test_cron_mis_cash_flow_generate_forecast_lines(self):
        sale_order_1 = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_2").id,
                "forecast_uninvoiced_amount": 100,
                "state": "sale",
            }
        )
        sale_order_2 = self.env["sale.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_3").id,
                "forecast_uninvoiced_amount": 200,
                "state": "done",
            }
        )
        sale_order_1.write(
            {"mis_cash_flow_forecast_line_ids": [(6, 0, [self.forecast_line1.id])]}
        )
        sale_order_2.write(
            {"mis_cash_flow_forecast_line_ids": [(6, 0, [self.forecast_line2.id])]}
        )

        self.env["sale.order"].cron_mis_cash_flow_generate_forecast_lines()
        self.assertTrue(sale_order_1.mis_cash_flow_forecast_line_ids)
        self.assertTrue(sale_order_2.mis_cash_flow_forecast_line_ids)
        self.assertEqual(len(sale_order_1.mis_cash_flow_forecast_line_ids), 1)
        self.assertEqual(len(sale_order_2.mis_cash_flow_forecast_line_ids), 1)
        orders = self.env["sale.order"].search(
            [
                ("forecast_uninvoiced_amount", ">", 0),
                ("state", "in", ["sale", "done"]),
            ],
            limit=100,
            offset=0,
        )
        orders.with_delay()._generate_mis_cash_flow_forecast_lines()
        self.assertNotEqual(len(orders), 0)

    def test_generate_mis_cash_flow_forecast_lines(self):
        rec = self.env["sale.order"].create(
            {
                "name": "Test Order",
                "partner_id": self.env.ref("base.res_partner_2").id,
                "company_id": self.env.ref("base.main_company").id,
                "expected_date": fields.Date.today(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "price_unit": 100,
                            "product_uom_qty": 2,
                        },
                    )
                ],
            }
        )
        rec.mis_cash_flow_forecast_line_ids.unlink()
        rec.state = "done"
        rec.forecast_uninvoiced_amount = 300
        rec.currency_id = self.currency_eur
        self.assertTrue(
            rec.forecast_uninvoiced_amount and rec.state in ["sale", "done"]
        )
        amount_uninvoiced = rec.forecast_uninvoiced_amount * 1
        self.assertEqual(amount_uninvoiced, 230)
        self.assertTrue(
            rec.currency_id
            and rec.company_id
            and rec.currency_id != rec.company_id.currency_id
        )
        amount_uninvoiced = rec.currency_id.round(amount_uninvoiced)
        self.assertEqual(amount_uninvoiced, 230)
        amount_uninvoiced_company = rec._compute_amount_uninvoiced_company_currency(
            amount_uninvoiced
        )
        self.assertEqual(round(amount_uninvoiced_company, 2), 351.65)
        payment_terms = rec._compute_payment_terms(
            rec.expected_date,
            round(amount_uninvoiced_company, 2),
            amount_uninvoiced,
        )
        expected_payment_terms = [
            (datetime.date.today().strftime("%Y-%m-%d"), 351.65, 230.0)
        ]
        self.assertEqual(len(payment_terms), 1)
        self.assertEqual(payment_terms, expected_payment_terms)
        self.assertEqual(len(rec._generate_mis_cash_flow_forecast_lines()), 1)

        rec.forecast_uninvoiced_amount = 100
        rec.state = "draft"
        self.assertEqual(len(rec._generate_mis_cash_flow_forecast_lines()), 0)
