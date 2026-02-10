# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestL10nBrMisBuilderCashFlowForecastSale(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.ref("base.main_company")
        cls.company.enable_sale_mis_cash_flow_forecast = True

        cls.account_receivable = cls.env["account.account"].create(
            {
                "name": "Receivable (BR test)",
                "code": "BRTREC",
                "account_type": "asset_receivable",
                "reconcile": True,
                "company_id": cls.company.id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Partner (BR test)",
                "company_id": cls.company.id,
                "property_account_receivable_id": cls.account_receivable.id,
            }
        )
        cls.company.partner_id.property_account_receivable_id = (
            cls.account_receivable.id
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Service (BR test)",
                "type": "service",
                "list_price": 100.0,
                "taxes_id": [(6, 0, [])],
                "supplier_taxes_id": [(6, 0, [])],
            }
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Pricelist (BR test)",
                "currency_id": cls.company.currency_id.id,
            }
        )

    def _create_sale_order(self, price_unit):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "pricelist_id": self.pricelist.id,
                "expected_date": fields.Date.today(),
            }
        )
        self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "name": self.product.name,
                "product_uom_qty": 1.0,
                "product_uom": self.product.uom_id.id,
                "price_unit": price_unit,
                "tax_id": [(6, 0, [])],
            }
        )
        order.write({"state": "sale"})
        return order

    def test_compute_uses_financial_total_on_brazilian_company(self):
        order = self._create_sale_order(price_unit=123.45)
        order._compute_forecast_uninvoiced_amount()

        self.assertEqual(order.company_id.country_id.code, "BR")
        self.assertEqual(order.forecast_uninvoiced_amount, order.amount_financial_total)
        self.assertNotEqual(order.forecast_uninvoiced_amount, order.amount_total)

    def test_generate_forecast_lines_respects_financial_total(self):
        order = self._create_sale_order(price_unit=200.0)
        order._compute_forecast_uninvoiced_amount()
        forecast_lines = order._generate_mis_cash_flow_forecast_lines()

        if order.amount_financial_total:
            self.assertTrue(forecast_lines)
            self.assertEqual(len(forecast_lines), 1)
            self.assertEqual(forecast_lines.balance, order.amount_financial_total)
        else:
            self.assertFalse(forecast_lines)

    def test_compute_sets_zero_when_order_is_canceled(self):
        order = self._create_sale_order(price_unit=150.0)
        order.write({"state": "cancel"})
        order._compute_forecast_uninvoiced_amount()
        self.assertEqual(order.forecast_uninvoiced_amount, 0.0)

    def test_compute_updates_stored_value_when_canceled(self):
        order = self._create_sale_order(price_unit=150.0)
        order.write({"forecast_uninvoiced_amount": 42.0, "state": "cancel"})
        order._compute_forecast_uninvoiced_amount()
        self.assertEqual(order.forecast_uninvoiced_amount, 0.0)
