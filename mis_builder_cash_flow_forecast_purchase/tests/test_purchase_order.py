# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged
from odoo.tools.translate import _


@tagged("post_install", "-at_install")
class TestPurchaseOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.current_date = fields.Datetime.now()
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
        cls.currency = cls.env.ref("base.USD")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Partner 1",
                "property_account_payable_id": cls.account_payable.id,
            }
        )
        cls.purchase_tax = cls.env["account.tax"].create(
            {
                "name": "Purchase Tax 10%",
                "amount": 10,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "company_id": cls.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Produto de Teste",
                "list_price": 10.0,
                "standard_price": 5.0,
                "currency_id": cls.currency.id,
                "supplier_taxes_id": [(6, 0, [cls.purchase_tax.id])],
            }
        )
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner.id,
                "date_order": cls.current_date,
                "company_id": cls.company.id,
            }
        )
        cls.purchase_order_line = cls.env["purchase.order.line"].create(
            {
                "order_id": cls.purchase_order.id,
                "product_id": cls.product.id,
                "product_qty": 10.0,
                "price_unit": cls.product.standard_price,
                "taxes_id": [(6, 0, [cls.purchase_tax.id])],
                "fiscal_tax_ids": [(6, 0, [cls.purchase_tax.id])],
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
        cls.invoice_1 = cls.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": cls.purchase_order.partner_id.id,
                "invoice_date": cls.current_date,
            }
        )
        cls.invoice_2 = cls.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": cls.purchase_order.partner_id.id,
                "invoice_date": cls.current_date,
            }
        )

    def test__compute_forecast_uninvoiced_amount(self):
        self.purchase_order.invoice_ids.unlink()
        self.purchase_order._compute_forecast_uninvoiced_amount()
        self.assertEqual(
            self.purchase_order.forecast_uninvoiced_amount,
            self.purchase_order.amount_total,
        )
        self.invoice_1.write({"state": "draft"})
        self.purchase_order._compute_forecast_uninvoiced_amount()
        self.assertEqual(
            self.purchase_order.forecast_uninvoiced_amount,
            self.purchase_order.amount_total - self.invoice_1.amount_total,
        )
        self.invoice_1.write({"state": "posted"})
        self.purchase_order._compute_forecast_uninvoiced_amount()
        self.assertEqual(
            self.purchase_order.forecast_uninvoiced_amount,
            self.purchase_order.amount_total - self.invoice_1.amount_total,
        )
        self.invoice_1.write({"state": "cancel"})
        self.purchase_order._compute_forecast_uninvoiced_amount()
        self.assertEqual(
            self.purchase_order.forecast_uninvoiced_amount,
            self.purchase_order.amount_total,
        )
        self.purchase_order._compute_forecast_uninvoiced_amount()
        self.assertEqual(
            self.purchase_order.forecast_uninvoiced_amount,
            self.purchase_order.amount_total
            - self.invoice_1.amount_total
            - self.invoice_2.amount_total,
        )

    def test_compute_mis_cash_flow_forecast_line_ids(self):
        self.purchase_order.button_confirm()
        self.invoice_1.invoice_line_ids.create(
            {
                "name": self.product.name,
                "move_id": self.invoice_1.id,
                "product_id": self.product.id,
                "account_id": (
                    self.product.categ_id.property_account_expense_categ_id.id
                ),
                "currency_id": self.currency.id,
            }
        )
        self.invoice_1.action_post()
        self.purchase_order._compute_mis_cash_flow_forecast_line_ids()
        forecast_lines = self.purchase_order.mis_cash_flow_forecast_line_ids
        self.assertEqual(len(forecast_lines), 0)

    def test_compute_payment_terms(self):
        self.purchase_order.payment_term_id = False
        total_balance = 1000.0
        total_amount_currency = 500.0
        expected_payment_terms = [
            (
                fields.Date.to_string(self.current_date),
                total_balance,
                total_amount_currency,
            )
        ]
        self.assertEqual(
            self.purchase_order._compute_payment_terms(
                self.current_date, total_balance, total_amount_currency
            ),
            expected_payment_terms,
        )

        payment_term = self.env["account.payment.term"].create(
            {
                "name": "Termo de Pagamento2",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 100.0,
                            "nb_days": 30,
                        },
                    )
                ],
            }
        )

        self.purchase_order.payment_term_id = payment_term.id
        expected_payment_terms = [
            (
                fields.Date.to_string(self.current_date + timedelta(days=30)),
                total_balance,
                total_balance,
            )
        ]
        self.assertEqual(
            self.purchase_order._compute_payment_terms(
                self.current_date, total_balance, total_balance
            ),
            expected_payment_terms,
        )

        payment_term = self.env["account.payment.term"].create(
            {
                "name": "Termo de Pagamento3",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "value": "percent",
                            "value_amount": 100.0,
                            "nb_days": 30,
                        },
                    )
                ],
            }
        )
        self.purchase_order.payment_term_id = payment_term.id
        self.purchase_order.currency_id = self.currency.id
        total_amount_currency = 1000.0
        expected_payment_terms = [
            (
                fields.Date.to_string(self.current_date + timedelta(days=30)),
                total_balance,
                total_amount_currency,
            )
        ]
        self.assertEqual(
            self.purchase_order._compute_payment_terms(
                self.current_date, total_balance, total_amount_currency
            ),
            expected_payment_terms,
        )

    def test_compute_amount_uninvoiced_company_currency(self):
        self.purchase_order.currency_id = False
        self.purchase_order.company_id = False
        expected_amount = 500.0
        self.assertEqual(
            self.purchase_order._compute_amount_uninvoiced_company_currency(
                expected_amount
            ),
            expected_amount,
        )
        self.purchase_order.currency_id = self.env.ref("base.USD").id
        self.purchase_order.company_id = self.env.ref("base.main_company").id
        expected_amount = 1000.0
        self.assertEqual(
            self.purchase_order._compute_amount_uninvoiced_company_currency(
                expected_amount
            ),
            expected_amount,
        )
        self.purchase_order.currency_id = self.env.ref("base.USD").id
        self.purchase_order.company_id = (
            self.env["res.company"]
            .create(
                {"name": "Test Company", "currency_id": self.env.ref("base.BRL").id}
            )
            .id
        )
        expected_amount = 1000.0
        self.assertEqual(
            self.purchase_order._compute_amount_uninvoiced_company_currency(1000.0),
            expected_amount,
        )

    def test__get_mis_cash_flow_forecast_update_trigger_fields(self):
        expected_fields = [
            "partner_id",
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
        actual_fields = (
            self.purchase_order._get_mis_cash_flow_forecast_update_trigger_fields()
        )
        self.assertEqual(actual_fields, expected_fields)

    def test_write(self):
        res = self.purchase_order.write({"state": "purchase"})
        self.assertTrue(res)
        self.purchase_order.write(
            {
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "price_unit": 300,
                        },
                    )
                ]
            }
        )
        self.assertFalse(self.purchase_order.mis_cash_flow_forecast_line_ids)

    def test_unlink(self):
        self.purchase_order._generate_mis_cash_flow_forecast_lines()
        self.purchase_order.state = "cancel"
        self.purchase_order.unlink()
        self.assertFalse(self.purchase_order.mis_cash_flow_forecast_line_ids)

    def test_prepare_mis_cash_flow_forecast_line(self):
        purchase_order = self.env["purchase.order"].create(
            {"partner_id": 1, "company_id": 1}
        )
        payment_term_item = "30"
        payment_term_count = 1
        date = self.current_date
        amount = 100.0
        expected_name = (
            f"{purchase_order.display_name} - {payment_term_item}/{payment_term_count}"
        )
        result = purchase_order._prepare_mis_cash_flow_forecast_line(
            payment_term_item, payment_term_count, date, amount
        )
        self.assertEqual(result["name"], expected_name)

        expected_account_id = (
            purchase_order.partner_id.property_account_payable_id.id
            or self.env["ir.property"]
            ._get("property_account_payable_id", "res.partner")
            .id
        )
        result = purchase_order._prepare_mis_cash_flow_forecast_line(
            payment_term_item, payment_term_count, date, amount
        )
        self.assertEqual(result["account_id"], expected_account_id)

        expected_partner_id = purchase_order.partner_id.id
        result = purchase_order._prepare_mis_cash_flow_forecast_line(
            payment_term_item, payment_term_count, date, amount
        )
        self.assertEqual(result["partner_id"], expected_partner_id)

        expected_balance = amount
        result = purchase_order._prepare_mis_cash_flow_forecast_line(
            payment_term_item, payment_term_count, date, amount
        )
        self.assertEqual(result["balance"], expected_balance)

        expected_company_id = purchase_order.company_id.id
        result = purchase_order._prepare_mis_cash_flow_forecast_line(
            payment_term_item, payment_term_count, date, amount
        )
        self.assertEqual(result["company_id"], expected_company_id)

        expected_parent_res_model_id = (
            self.env["ir.model"]._get(purchase_order._name).id
        )
        expected_parent_res_id = purchase_order.id
        result = purchase_order._prepare_mis_cash_flow_forecast_line(
            payment_term_item, payment_term_count, date, amount
        )
        self.assertEqual(result["parent_res_model_id"], expected_parent_res_model_id)
        self.assertEqual(result["parent_res_id"], expected_parent_res_id)

    def test_generate_mis_cash_flow_forecast_lines(self):
        self.purchase_order.forecast_uninvoiced_amount = 100.0
        self.purchase_order.state = "purchase"
        self.purchase_order._generate_mis_cash_flow_forecast_lines()
        self.assertEqual(len(self.purchase_order.mis_cash_flow_forecast_line_ids), 0)

    def test_cron_mis_cash_flow_generate_forecast_lines(self):
        self.purchase_order.button_confirm()
        self.purchase_order.button_done()
        self.env["purchase.order"].cron_mis_cash_flow_generate_forecast_lines()
        forecast_lines = self.env["mis.cash_flow.forecast_line"].search([])
        self.assertEqual(len(forecast_lines), 0)

    def test_action_show_mis_forecast(self):
        action = self.purchase_order.action_show_mis_forecast()
        expected_context = dict(self.env.context)
        expected_context.pop("group_by", None)
        expected_values = {
            "type": "ir.actions.act_window",
            "name": _("Cash Flow Forecast - Purchase"),
            "res_model": "mis.cash_flow.forecast_line",
            "domain": [
                ("parent_res_model", "=", self.purchase_order._name),
                ("parent_res_id", "=", self.purchase_order.id),
            ],
            "view_mode": "pivot,tree",
            "context": expected_context,
        }
        self.assertDictEqual(action, expected_values)
        self.assertEqual(action["name"], expected_values["name"])
        self.assertEqual(action["res_model"], expected_values["res_model"])
        self.assertEqual(action["domain"], expected_values["domain"])
        self.assertEqual(action["view_mode"], expected_values["view_mode"])
        self.assertEqual(action["context"], expected_values["context"])
