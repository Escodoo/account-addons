# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseNonFiscalTotal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Fornecedor Teste"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Serviço Teste",
                "type": "service",
                "supplier_taxes_id": [(5, 0, 0)],
            }
        )

    def test_total_without_fiscal_operation(self):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "fiscal_operation_id": False,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 2,
                            "price_unit": 150.0,
                            "fiscal_operation_id": False,
                        },
                    )
                ],
            }
        )
        self.assertFalse(order.fiscal_operation_id)
        self.assertEqual(order.amount_total, 300.0)
        self.assertEqual(order.tax_totals["total_amount_currency"], 300.0)
