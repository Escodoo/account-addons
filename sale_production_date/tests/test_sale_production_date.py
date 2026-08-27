# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestSaleProductionDate(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_obj = cls.env["sale.order"]
        cls.production_date = datetime.now().date() + timedelta(days=2)
        cls.account_receivable = cls.env["account.account"].create(
            {
                "name": "Receivable (test)",
                "code": "TREC",
                "account_type": "asset_receivable",
                "reconcile": True,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Partner (test)",
                "property_account_receivable_id": cls.account_receivable.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "detailed_type": "consu",
                "invoice_policy": "order",
                "list_price": 100.0,
            }
        )
        cls.analytic_plan = cls.env["account.analytic.plan"].create(
            {"name": "Plan (test)"}
        )
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {"name": "Analytic (test)", "plan_id": cls.analytic_plan.id}
        )

    def _create_sale_order(self, production_date=False, analytic=False):
        line_vals = {
            "product_id": self.product.id,
            "product_uom_qty": 1.0,
        }
        if analytic:
            line_vals["analytic_distribution"] = {str(self.analytic_account.id): 100}
        order_vals = {
            "partner_id": self.partner.id,
            "production_date": production_date,
            "order_line": [(0, 0, line_vals)],
        }
        order = self.sale_obj.create(order_vals)
        # Keep the order out of the fiscal operation flow.
        if "fiscal_operation_id" in order._fields:
            order.fiscal_operation_id = False
        return order

    def test_prepare_invoice_propagates_production_date(self):
        order = self._create_sale_order(production_date=self.production_date)
        invoice_vals = order._prepare_invoice()
        self.assertEqual(invoice_vals.get("production_date"), self.production_date)

    def test_prepare_invoice_without_production_date(self):
        order = self._create_sale_order()
        invoice_vals = order._prepare_invoice()
        self.assertNotIn("production_date", invoice_vals)

    def test_create_invoices_sets_production_date_on_move(self):
        order = self._create_sale_order(production_date=self.production_date)
        order.action_confirm()
        invoice = order._create_invoices(final=True)
        self.assertEqual(invoice.production_date, self.production_date)

    def test_production_date_not_copied(self):
        order = self._create_sale_order(production_date=self.production_date)
        order.action_confirm()
        invoice = order._create_invoices(final=True)
        self.assertFalse(invoice.copy().production_date)

    def test_post_updates_analytic_line_dates(self):
        order = self._create_sale_order(
            production_date=self.production_date, analytic=True
        )
        order.action_confirm()
        invoice = order._create_invoices(final=True)
        invoice.action_post()

        analytic_lines = invoice.line_ids.analytic_line_ids
        self.assertTrue(analytic_lines)
        for line in analytic_lines:
            self.assertEqual(line.date, self.production_date)

    def test_post_without_production_date_keeps_default_dates(self):
        order = self._create_sale_order(analytic=True)
        order.action_confirm()
        invoice = order._create_invoices(final=True)
        invoice.action_post()

        analytic_lines = invoice.line_ids.analytic_line_ids
        self.assertTrue(analytic_lines)
        for line in analytic_lines:
            self.assertNotEqual(line.date, self.production_date)
