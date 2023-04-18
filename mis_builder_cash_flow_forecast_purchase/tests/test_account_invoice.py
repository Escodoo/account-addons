# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountMove(TransactionCase):
    def setUp(self):
        super(TestAccountMove, self).setUp()
        self.current_date = datetime.today()
        self.company = self.env.ref("base.main_company")
        self.currency = self.env.ref("base.USD")
        self.partner = self.env["res.partner"].create({"name": "Partner 1"})
        self.product = self.env["product.product"].create(
            {
                "name": "Produto de Teste",
                "list_price": 10.0,
                "standard_price": 5.0,
            }
        )
        self.purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
            }
        )
        self.purchase_order_line = self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "product_id": self.product.id,
                "product_qty": 10.0,
                "price_unit": self.product.standard_price,
            }
        )
        self.account_move = self.env["account.move"].create(
            {
                "name": "Movimentação de Teste",
            }
        )
        self.invoice_line = self.env["account.move.line"].create(
            {
                "move_id": self.account_move.id,
                "name": self.product.name,
                "product_id": self.product.id,
                "quantity": 5.0,
                "price_unit": self.product.list_price,
                "account_id": self.partner.property_account_payable_id.id,
                "purchase_line_id": self.purchase_order_line.id,
            }
        )

    def test_action_post(self):
        self.account_move.action_post()
        order = self.account_move.invoice_line_ids.mapped("purchase_line_id.order_id")
        self.assertTrue(
            order and order.company_id.enable_purchase_mis_cash_flow_forecast
        )
        self.assertTrue(order.with_delay()._generate_mis_cash_flow_forecast_lines())

    def test_button_cancel(self):
        self.account_move.button_cancel()
        order = self.account_move.invoice_line_ids.mapped("purchase_line_id.order_id")
        self.assertTrue(
            order and order.company_id.enable_purchase_mis_cash_flow_forecast
        )
        order._compute_forecast_uninvoiced_amount()
        order.with_delay()._generate_mis_cash_flow_forecast_lines()
        self.assertEqual(
            order.forecast_uninvoiced_amount, self.purchase_order_line.price_total
        )

    def test_button_draft(self):
        self.account_move.button_draft()
        order = self.account_move.invoice_line_ids.mapped("purchase_line_id.order_id")
        self.assertTrue(
            order and order.company_id.enable_purchase_mis_cash_flow_forecast
        )
        order._compute_forecast_uninvoiced_amount()
        order.with_delay()._generate_mis_cash_flow_forecast_lines()
        self.assertEqual(
            order.forecast_uninvoiced_amount, self.purchase_order_line.price_total
        )

    def test_create(self):
        move_vals = {
            "name": "Movimentação de Teste",
        }
        move = self.env["account.move"].create(move_vals)
        invoice_line_vals = {
            "move_id": move.id,
            "name": self.product.name,
            "product_id": self.product.id,
            "quantity": 5.0,
            "price_unit": self.product.list_price,
            "account_id": self.partner.property_account_payable_id.id,
            "purchase_line_id": self.purchase_order_line.id,
        }
        self.env["account.move.line"].create(invoice_line_vals)
        order = self.account_move.invoice_line_ids.mapped("purchase_line_id.order_id")
        self.assertTrue(
            order and order.company_id.enable_purchase_mis_cash_flow_forecast
        )
        order._compute_forecast_uninvoiced_amount()
        order.with_delay()._generate_mis_cash_flow_forecast_lines()
        self.assertEqual(
            order.forecast_uninvoiced_amount, self.purchase_order_line.price_total
        )
