# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMisBuilderCashFlowForecastSale(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.ref("base.main_company")
        cls.company.country_id = cls.env.ref("base.us")
        cls.company.enable_sale_mis_cash_flow_forecast = True

        # Load US chart of accounts for proper accounting setup
        cls.env["account.chart.template"].try_loading(
            "generic_coa", company=cls.company, install_demo=False
        )

        # Use existing accounts from the chart instead of creating new ones
        cls.account_receivable = cls.env["account.account"].search(
            [
                ("account_type", "=", "asset_receivable"),
                ("company_ids", "in", cls.company.id),
            ],
            limit=1,
        )
        cls.account_income = cls.env["account.account"].search(
            [
                ("account_type", "=", "income"),
                ("company_ids", "in", cls.company.id),
            ],
            limit=1,
        )

        # Garante receivable no parceiro e no parceiro da empresa
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Partner (test)",
                "company_id": cls.company.id,
                "property_account_receivable_id": cls.account_receivable.id,
            }
        )
        cls.company.partner_id.property_account_receivable_id = (
            cls.account_receivable.id
        )

        cls.partner2 = cls.env["res.partner"].create(
            {
                "name": "Partner 2 (test)",
                "company_id": cls.company.id,
                "property_account_receivable_id": cls.account_receivable.id,
            }
        )

        cls.product = cls.env["product.product"].create(
            {
                "name": "Service (test)",
                "type": "service",
                "list_price": 100.0,
                # Em bases com l10n_br_* pode existir imposto default.
                # Para estes testes, queremos isolar e evitar compute de impostos.
                "taxes_id": [(6, 0, [])],
                "supplier_taxes_id": [(6, 0, [])],
            }
        )

        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Pricelist (test)",
                "currency_id": cls.company.currency_id.id,
            }
        )

        cls.journal_sale = cls.env["account.journal"].create(
            {
                "name": "Sales Journal (test)",
                "code": "TSJ",
                "type": "sale",
                "company_id": cls.company.id,
            }
        )

    def _create_sale_order(self, price_unit=100.0):
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
                # Evita disparar lógica de impostos/localização (ex.: l10n_br_account)
                "tax_id": [(6, 0, [])],
            }
        )
        # Evita dependências do fluxo completo (stock/pickings/etc)
        order.write({"state": "sale"})
        return order

    def _create_invoice_move_linked_to_sale_line(self, sale_line, price_unit=100.0):
        # Criamos uma fatura em draft com invoice_line_ids já linkada à sale_line.
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "journal_id": self.journal_sale.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "INV line (test)",
                            "product_id": self.product.id,
                            "quantity": 1.0,
                            "price_unit": price_unit,
                            "account_id": self.account_income.id,
                            # Evita compute de impostos/localização no invoice line
                            "tax_ids": [(6, 0, [])],
                            "sale_line_ids": [(6, 0, [sale_line.id])],
                        },
                    )
                ],
            }
        )

    def test_compute_forecast_uninvoiced_amount_no_invoices(self):
        order = self._create_sale_order(price_unit=123.45)
        order._compute_forecast_uninvoiced_amount()
        self.assertEqual(order.forecast_uninvoiced_amount, order.amount_total)

    def test_compute_forecast_uninvoiced_amount_cancel_is_zero(self):
        order = self._create_sale_order(price_unit=50.0)
        order.write({"state": "cancel"})
        order._compute_forecast_uninvoiced_amount()
        self.assertEqual(order.forecast_uninvoiced_amount, 0)

    def test_generate_forecast_lines_creates_records(self):
        order = self._create_sale_order(price_unit=200.0)
        order._compute_forecast_uninvoiced_amount()

        forecast_lines = order._generate_mis_cash_flow_forecast_lines()
        self.assertTrue(forecast_lines)
        self.assertEqual(len(forecast_lines), 1)

        fl = forecast_lines[0]
        self.assertEqual(fl.company_id, self.company)
        self.assertEqual(fl.partner_id, order.partner_id)
        self.assertEqual(fl.res_model, "sale.order")
        self.assertEqual(fl.res_id, order.id)
        self.assertEqual(fl.parent_res_model, "sale.order")
        self.assertEqual(fl.parent_res_id, order.id)
        self.assertEqual(fl.balance, order.amount_total)

        # Campos computados do pedido
        order.invalidate_recordset()
        self.assertEqual(order.mis_cash_flow_forecast_line_count, 1)

    def test_unlink_sale_order_deletes_forecast_lines(self):
        order = self._create_sale_order(price_unit=80.0)
        order._compute_forecast_uninvoiced_amount()
        order._generate_mis_cash_flow_forecast_lines()
        order_id = order.id

        ForecastLine = self.env["mis.cash_flow.forecast_line"]
        existing = ForecastLine.search(
            [
                ("parent_res_model", "=", "sale.order"),
                ("parent_res_id", "=", order_id),
            ]
        )
        self.assertTrue(existing)

        # Odoo não permite deletar pedido confirmado; precisa cancelar antes.
        order.write({"state": "cancel"})
        order.unlink()

        remaining = ForecastLine.search(
            [
                ("parent_res_model", "=", "sale.order"),
                ("parent_res_id", "=", order_id),
            ]
        )
        self.assertFalse(remaining)

    def test_write_triggers_generation_when_sale(self):
        order = self._create_sale_order(price_unit=10.0)
        SaleOrderModel = type(order)

        def _with_delay(self, *args, **kwargs):
            return self

        with (
            patch.object(
                SaleOrderModel,
                "with_delay",
                autospec=True,
                side_effect=_with_delay,
            ),
            patch.object(
                SaleOrderModel, "_generate_mis_cash_flow_forecast_lines", autospec=True
            ) as gen,
        ):
            order.write({"partner_id": self.partner2.id})
            self.assertGreaterEqual(gen.call_count, 1)

    def test_account_move_action_post_triggers_generation(self):
        order = self._create_sale_order(price_unit=100.0)
        move = self._create_invoice_move_linked_to_sale_line(order.order_line[:1])
        SaleOrderModel = type(order)

        def _with_delay(self, *args, **kwargs):
            return self

        # Evita postar de verdade (precisaria de configuração completa contábil)
        with (
            patch(
                "odoo.addons.account.models.account_move.AccountMove.action_post",
                autospec=True,
                return_value=True,
            ),
            patch.object(
                SaleOrderModel,
                "with_delay",
                autospec=True,
                side_effect=_with_delay,
            ),
            patch.object(
                SaleOrderModel, "_generate_mis_cash_flow_forecast_lines", autospec=True
            ) as gen,
        ):
            move.action_post()
            self.assertGreaterEqual(gen.call_count, 1)

    def test_account_move_button_cancel_triggers_compute_and_generation(self):
        order = self._create_sale_order(price_unit=100.0)
        move = self._create_invoice_move_linked_to_sale_line(order.order_line[:1])
        SaleOrderModel = type(order)

        def _with_delay(self, *args, **kwargs):
            return self

        with (
            patch(
                "odoo.addons.account.models.account_move.AccountMove.button_cancel",
                autospec=True,
                return_value=True,
            ),
            patch.object(
                SaleOrderModel,
                "with_delay",
                autospec=True,
                side_effect=_with_delay,
            ),
            patch.object(
                SaleOrderModel, "_compute_forecast_uninvoiced_amount", autospec=True
            ) as comp,
            patch.object(
                SaleOrderModel, "_generate_mis_cash_flow_forecast_lines", autospec=True
            ) as gen,
        ):
            move.button_cancel()
            self.assertGreaterEqual(comp.call_count, 1)
            self.assertGreaterEqual(gen.call_count, 1)

    def test_account_move_button_draft_triggers_compute_and_generation(self):
        order = self._create_sale_order(price_unit=100.0)
        move = self._create_invoice_move_linked_to_sale_line(order.order_line[:1])
        SaleOrderModel = type(order)

        def _with_delay(self, *args, **kwargs):
            return self

        with (
            patch(
                "odoo.addons.account.models.account_move.AccountMove.button_draft",
                autospec=True,
                return_value=True,
            ),
            patch.object(
                SaleOrderModel,
                "with_delay",
                autospec=True,
                side_effect=_with_delay,
            ),
            patch.object(
                SaleOrderModel, "_compute_forecast_uninvoiced_amount", autospec=True
            ) as comp,
            patch.object(
                SaleOrderModel, "_generate_mis_cash_flow_forecast_lines", autospec=True
            ) as gen,
        ):
            move.button_draft()
            self.assertGreaterEqual(comp.call_count, 1)
            self.assertGreaterEqual(gen.call_count, 1)

    def test_account_move_create_triggers_compute_and_generation(self):
        order = self._create_sale_order(price_unit=100.0)
        sale_line = order.order_line[:1]
        SaleOrderModel = type(order)

        def _with_delay(self, *args, **kwargs):
            return self

        with (
            patch.object(
                SaleOrderModel,
                "with_delay",
                autospec=True,
                side_effect=_with_delay,
            ),
            patch.object(
                SaleOrderModel, "_compute_forecast_uninvoiced_amount", autospec=True
            ) as comp,
            patch.object(
                SaleOrderModel, "_generate_mis_cash_flow_forecast_lines", autospec=True
            ) as gen,
        ):
            self.env["account.move"].create(
                {
                    "move_type": "out_invoice",
                    "partner_id": self.partner.id,
                    "company_id": self.company.id,
                    "journal_id": self.journal_sale.id,
                    "invoice_date": fields.Date.today(),
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "INV line (test)",
                                "product_id": self.product.id,
                                "quantity": 1.0,
                                "price_unit": 100.0,
                                "account_id": self.account_income.id,
                                "tax_ids": [(6, 0, [])],
                                "sale_line_ids": [(6, 0, [sale_line.id])],
                            },
                        )
                    ],
                }
            )
            self.assertGreaterEqual(comp.call_count, 1)
            self.assertGreaterEqual(gen.call_count, 1)
