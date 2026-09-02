# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountMove(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.company.country_id = cls.env.ref("base.us")
        cls.company.enable_purchase_mis_cash_flow_forecast = True
        cls.env["account.chart.template"].try_loading(
            "generic_coa", company=cls.company, install_demo=False
        )
        cls.account_payable = cls.env["account.account"].search(
            [("account_type", "=", "liability_payable")], limit=1
        )
        cls.account_expense = cls.env["account.account"].search(
            [("account_type", "=", "expense")], limit=1
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Partner 1",
                "property_account_payable_id": cls.account_payable.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Produto de Teste",
                "list_price": 10.0,
                "standard_price": 5.0,
            }
        )
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner.id,
            }
        )
        cls.purchase_order_line = cls.env["purchase.order.line"].create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.product.id,
                "product_qty": 10.0,
                "price_unit": cls.product.standard_price,
            }
        )
        cls.account_move = cls.env["account.move"].create(
            {
                "name": "Movimentação de Teste",
            }
        )
        cls.invoice_line = cls.env["account.move.line"].create(
            {
                "move_id": cls.account_move.id,
                "name": cls.product.name,
                "product_id": cls.product.id,
                "quantity": 5.0,
                "price_unit": cls.product.list_price,
                "account_id": cls.account_payable.id,
                "purchase_line_id": cls.purchase_order_line.id,
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
        self.account_move.action_post()
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
