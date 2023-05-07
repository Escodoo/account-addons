# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAccountInvoice(TransactionCase):
    def setUp(self):
        super(TestAccountInvoice, self).setUp()
        self.company = self.env["res.company"].create({"name": "Test Company"})
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
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

    def test_action_post(self):
        self.company.enable_sale_mis_cash_flow_forecast = True
        self.account_move.invoice_line_ids.sale_line_ids = self.sale_order.order_line
        self.account_move.action_post()
        order = self.account_move.invoice_line_ids.mapped("sale_line_ids.order_id")
        self.assertTrue(order and order.company_id.enable_sale_mis_cash_flow_forecast)
        order.with_delay()._generate_mis_cash_flow_forecast_lines()

    def test_button_cancel(self):
        self.company.enable_sale_mis_cash_flow_forecast = True
        self.account_move.invoice_line_ids.sale_line_ids = self.sale_order.order_line
        self.account_move.button_cancel()
        order = self.account_move.invoice_line_ids.mapped("sale_line_ids.order_id")
        self.assertTrue(order and order.company_id.enable_sale_mis_cash_flow_forecast)
        order._compute_forecast_uninvoiced_amount()
        order.with_delay()._generate_mis_cash_flow_forecast_lines()

    def test_button_draft(self):
        self.company.enable_sale_mis_cash_flow_forecast = True
        self.account_move.invoice_line_ids.sale_line_ids = self.sale_order.order_line
        self.account_move.button_draft()
        order = self.account_move.invoice_line_ids.mapped("sale_line_ids.order_id")
        self.assertTrue(order and order.company_id.enable_sale_mis_cash_flow_forecast)
        order._compute_forecast_uninvoiced_amount()
        order.with_delay()._generate_mis_cash_flow_forecast_lines()

    def test_create(self):

        vals_list = [
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "date": "2022-01-01",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "invoice_line2",
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                        },
                    ),
                ],
            }
        ]
        moves = self.env["account.move"].create(vals_list)
        moves.invoice_line_ids.sale_line_ids = self.sale_order.order_line
        self.company.enable_sale_mis_cash_flow_forecast = True
        order = moves.invoice_line_ids.mapped("sale_line_ids.order_id")
        self.assertTrue(order and order.company_id.enable_sale_mis_cash_flow_forecast)
        order._compute_forecast_uninvoiced_amount()
        order.with_delay()._generate_mis_cash_flow_forecast_lines()
