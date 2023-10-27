# Copyright 2023 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from datetime import date, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestSaleBlanketOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.blanket_order_obj = self.env["sale.blanket.order"]
        self.blanket_order_line_obj = self.env["sale.blanket.order.line"]
        self.blanket_order_wiz_obj = self.env["sale.blanket.order.wizard"]
        self.so_obj = self.env["sale.order"]
        self.payment_term = self.env.ref("account.account_payment_term_immediate")
        self.sale_pricelist = self.env["product.pricelist"].create(
            {"name": "Test Pricelist", "currency_id": self.env.ref("base.USD").id}
        )
        # UoM
        self.categ_unit = self.env.ref("uom.product_uom_categ_unit")
        self.uom_dozen = self.env["uom.uom"].create(
            {
                "name": "Test-DozenA",
                "category_id": self.categ_unit.id,
                "factor_inv": 12,
                "uom_type": "bigger",
                "rounding": 0.001,
            }
        )

        self.partner = self.env["res.partner"].create(
            {
                "name": "TEST CUSTOMER",
                "property_product_pricelist": self.sale_pricelist.id,
            }
        )
        self.partner2 = self.env["res.partner"].create(
            {
                "name": "TEST CUSTOMER2",
                "property_product_pricelist": self.sale_pricelist.id,
            }
        )

        self.product = self.env.ref("product.product_product_4")
        self.product2 = self.env.ref("product.product_product_5")

        self.yesterday = fields.Date.to_string(date.today() - timedelta(days=1))
        self.tomorrow = fields.Date.to_string(date.today() + timedelta(days=1))

    def test_forecast_sale_blanket_order(self):
        blanket_order = self.blanket_order_obj.create(
            {
                "partner_id": self.partner.id,
                "validity_date": self.tomorrow,
                "payment_term_id": self.payment_term.id,
                "pricelist_id": self.sale_pricelist.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "original_uom_qty": 5.0,
                            "price_unit": 20.00,
                        },
                    )
                ],
            }
        )
        self.assertEqual(blanket_order.state, "draft")

        blanket_order.sudo().action_confirm()
        self.assertEqual(blanket_order.state, "open")

        blanket_order._compute_forecast_uninvoiced_amount()

        self.assertEqual(blanket_order.forecast_uninvoiced_amount, 100.0)

        wizard = self.blanket_order_wiz_obj.with_context(
            active_id=blanket_order.id, active_model="sale.blanket.order"
        ).create({})
        wizard.line_ids[0].write({"qty": 3.0})
        wizard.sudo().create_sale_order()

        payment_term_result = blanket_order._compute_payment_terms(
            self.tomorrow, 100.0, 100.0
        )
        expected_result = [(self.tomorrow, 100.0, 100.0)]

        self.assertEqual(payment_term_result, expected_result)

        amount_uninvoiced = 100.0
        amount_result = blanket_order._compute_amount_uninvoiced_company_currency(
            amount_uninvoiced
        )
        expected_result = 100.0

        self.assertEqual(amount_result, expected_result)
        self.assertEqual(blanket_order.forecast_uninvoiced_amount, 40.0)

        wizard.line_ids[0].write({"qty": 2.0})
        wizard.sudo().create_sale_order()

        self.assertEqual(blanket_order.forecast_uninvoiced_amount, 0.0)
        self.assertEqual(
            blanket_order.currency_id, blanket_order.company_id.currency_id
        )

        for sale_order in blanket_order.line_ids.sale_lines.order_id:
            self.assertEqual(sale_order.state, "draft")

        fields = blanket_order._get_mis_cash_flow_forecast_update_trigger_fields()
        expected_fields = [
            "partner_id",
            "pricelist_id",
            "fiscal_position_id",
            "currency_id",
            "line_ids",
            "payment_term_id",
            "state",
            "line_ids.sale_lines.order_id",
            "sale_count",
        ]
        self.assertEqual(fields, expected_fields)

        values = {"state": "open", "partner_id": self.partner2.id}
        job_count_before = self.env["queue.job"].search_count([])
        blanket_order.write(values)
        job_count_after = self.env["queue.job"].search_count([])

        self.assertEqual(job_count_after, job_count_before + 1)

        last_job = self.env["queue.job"].search([], order="id desc", limit=1)

        self.assertEqual(last_job.state, "pending")

        payment_term_item = 1
        payment_term_count = 1
        date = self.tomorrow
        amount = 100.0

        result_prepare_forecast = blanket_order._prepare_mis_cash_flow_forecast_line(
            payment_term_item, payment_term_count, date, amount
        )

        expected_result = {
            "name": "%s - %s/%s"
            % (blanket_order.display_name, payment_term_item, payment_term_count),
            "date": date,
            "account_id": self.partner.property_account_receivable_id.id
            or self.env.ref("property_account_receivable_id"),
            "partner_id": self.partner2.id,
            "balance": amount,
            "company_id": blanket_order.company_id.id,
            "res_model_id": self.env["ir.model"]._get(blanket_order._name).id,
            "res_id": blanket_order.id,
            "parent_res_model_id": self.env["ir.model"]._get(blanket_order._name).id,
            "parent_res_id": blanket_order.id,
        }

        self.assertEqual(result_prepare_forecast, expected_result)

        blanket_order.cron_mis_cash_flow_generate_forecast_lines()
        orders = blanket_order.search(
            [
                ("forecast_uninvoiced_amount", ">", 0),
                ("state", "in", ["open", "done"]),
            ]
        )
        for order in orders:
            self.assertTrue(order.mis_cash_flow_forecast_line_ids)
        processed_orders = self.blanket_order_obj.search(
            [
                ("forecast_uninvoiced_amount", ">", 0),
                ("state", "in", ["open", "done"]),
            ]
        )
        self.assertEqual(len(processed_orders), len(orders))
