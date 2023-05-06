# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestContractLine(TransactionCase):
    def setUp(self):
        super(TestContractLine, self).setUp()
        self.today = fields.Date.today()
        self.pricelist = self.env["product.pricelist"].create(
            {"name": "pricelist for contract test"}
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "partner test contract",
                "property_product_pricelist": self.pricelist.id,
                "email": "demo@demo.com",
            }
        )
        self.product_1 = self.env.ref("product.product_product_1")
        self.product_2 = self.env.ref("product.product_product_2")
        self.product_1.taxes_id += self.env["account.tax"].search(
            [("type_tax_use", "=", "sale")], limit=1
        )
        self.product_1.description_sale = "Test description sale"
        self.line_template_vals = {
            "product_id": self.product_1.id,
            "name": "contract",
            "quantity": 1,
            "uom_id": self.product_1.uom_id.id,
            "price_unit": 100,
            "discount": 50,
            "recurring_rule_type": "yearly",
            "recurring_interval": 1,
        }
        self.section_template_vals = {
            "display_type": "line_section",
            "name": "Test section",
        }
        self.template_vals = {
            "name": "Test Contract Template",
            "contract_line_ids": [
                (0, 0, self.section_template_vals),
                (0, 0, self.line_template_vals),
            ],
        }
        self.template = self.env["contract.template"].create(self.template_vals)
        # For being sure of the applied price
        self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.partner.property_product_pricelist.id,
                "product_id": self.product_1.id,
                "compute_price": "formula",
                "base": "list_price",
            }
        )
        self.contract = self.env["contract.contract"].create(
            {
                "name": "Test Contract",
                "partner_id": self.partner.id,
                "pricelist_id": self.partner.property_product_pricelist.id,
                "line_recurrence": True,
            }
        )
        self.contract2 = self.env["contract.contract"].create(
            {
                "name": "Test Contract 2",
                "partner_id": self.partner.id,
                "pricelist_id": self.partner.property_product_pricelist.id,
                "line_recurrence": True,
                "contract_type": "purchase",
                "contract_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_1.id,
                            "name": "contract",
                            "quantity": 1,
                            "uom_id": self.product_1.uom_id.id,
                            "price_unit": 100,
                            "discount": 50,
                            "recurring_rule_type": "monthly",
                            "recurring_interval": 1,
                            "date_start": "2018-02-15",
                            "recurring_next_date": "2018-02-22",
                        },
                    )
                ],
            }
        )
        self.acct_line = self.env["contract.line"].create(
            {
                "contract_id": self.contract.id,
                "product_id": self.product_1.id,
                "name": "contract",
                "quantity": 1,
                "uom_id": self.product_1.uom_id.id,
                "price_unit": 100,
                "discount": 50,
                "recurring_rule_type": "monthly",
                "recurring_interval": 1,
                "date_start": "2018-01-01",
                "recurring_next_date": (
                    fields.Date.today() - timedelta(days=1)
                ).strftime("%Y-%m-%d"),
                "is_auto_renew": False,
            }
        )
        self.contract.company_id.create_new_line_at_contract_line_renew = True
        self.terminate_reason = self.env["contract.terminate.reason"].create(
            {"name": "terminate_reason"}
        )

        self.contract3 = self.env["contract.contract"].create(
            {
                "name": "Test Contract 3",
                "partner_id": self.partner.id,
                "pricelist_id": self.partner.property_product_pricelist.id,
                "line_recurrence": False,
                "contract_type": "sale",
                "recurring_interval": 1,
                "recurring_rule_type": "monthly",
                "date_start": "2018-02-15",
                "contract_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": False,
                            "name": "Header for Services",
                            "display_type": "line_section",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": False,
                            "name": "contract",
                            "quantity": 1,
                            "price_unit": 100,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": False,
                            "name": "Line",
                            "quantity": 1,
                            "price_unit": 120,
                        },
                    ),
                ],
            }
        )

    def test_prepare_mis_cash_flow_forecast_line_sale(self):
        data = self.acct_line._prepare_mis_cash_flow_forecast_line(
            period_date_start=fields.Date.today(),
            period_date_end=fields.Date.today(),
            recurring_next_date=fields.Date.today(),
        )
        self.assertEqual(
            data["name"],
            f"{self.contract.display_name} - contract",
        )
        self.assertEqual(data["date"], fields.Date.today())
        self.assertEqual(
            data["account_id"],
            self.contract.partner_id.property_account_receivable_id.id,
        )
        self.assertEqual(data["partner_id"], self.contract.partner_id.id)
        self.assertEqual(data["balance"], 50.0)
        self.assertEqual(data["company_id"], self.contract.company_id.id)
        self.assertEqual(
            data["res_model_id"], self.env["ir.model"]._get(self.acct_line._name).id
        )
        self.assertEqual(data["res_id"], self.acct_line.id)
        self.assertEqual(
            data["parent_res_model_id"],
            self.env["ir.model"]._get(self.contract._name).id,
        )
        self.assertEqual(data["parent_res_id"], self.contract.id)

    def test_prepare_mis_cash_flow_forecast_line_purchase(self):
        self.contract.contract_type = "purchase"
        data = self.acct_line._prepare_mis_cash_flow_forecast_line(
            period_date_start=fields.Date.today(),
            period_date_end=fields.Date.today(),
            recurring_next_date=fields.Date.today(),
        )
        self.assertEqual(
            data["name"],
            f"{self.contract.display_name} - contract",
        )
        self.assertEqual(data["date"], fields.Date.today())
        self.assertEqual(
            data["account_id"], self.contract.partner_id.property_account_payable_id.id
        )
        self.assertEqual(data["partner_id"], self.contract.partner_id.id)
        self.assertEqual(data["balance"], -50.0)
        self.assertEqual(data["company_id"], self.contract.company_id.id)
        self.assertEqual(
            data["res_model_id"], self.env["ir.model"]._get(self.acct_line._name).id
        )
        self.assertEqual(data["res_id"], self.acct_line.id)
        self.assertEqual(
            data["parent_res_model_id"],
            self.env["ir.model"]._get(self.contract._name).id,
        )
        self.assertEqual(data["parent_res_id"], self.contract.id)

    def test_get_mis_cash_flow_contract_forecast_end_date(self):
        self.contract.company_id.write(
            {
                "contract_mis_cash_flow_forecast_rule_type": "monthly",
                "contract_mis_cash_flow_forecast_interval": 2,
            }
        )
        expected_date = fields.Date.today() + relativedelta(months=2)
        self.assertEqual(
            self.acct_line._get_mis_cash_flow_contract_forecast_end_date(),
            expected_date,
        )
        self.contract.company_id.write(
            {
                "contract_mis_cash_flow_forecast_rule_type": "yearly",
                "contract_mis_cash_flow_forecast_interval": 2,
            }
        )
        expected_date = fields.Date.today() + relativedelta(years=2)
        self.assertEqual(
            self.acct_line._get_mis_cash_flow_contract_forecast_end_date(),
            expected_date,
        )

    def test_get_generate_mis_cash_flow_forecast_line_criteria(self):
        self.contract.company_id.enable_contract_mis_cash_flow_forecast = False
        period_date_end = date(2023, 5, 31)
        self.assertFalse(
            self.acct_line._get_generate_mis_cash_flow_forecast_line_criteria(
                period_date_end
            )
        )

        self.contract.company_id.enable_contract_mis_cash_flow_forecast = True
        self.acct_line.is_canceled = True
        period_date_end = date(2023, 5, 31)
        self.assertFalse(
            self.acct_line._get_generate_mis_cash_flow_forecast_line_criteria(
                period_date_end
            )
        )

        self.acct_line.is_canceled = False
        self.acct_line.active = False
        period_date_end = date(2023, 5, 31)
        self.assertFalse(
            self.acct_line._get_generate_mis_cash_flow_forecast_line_criteria(
                period_date_end
            )
        )

        self.acct_line.active = True
        self.acct_line.is_auto_renew = False
        period_date_end = date(2023, 7, 31)
        self.assertTrue(
            self.acct_line._get_generate_mis_cash_flow_forecast_line_criteria(
                period_date_end
            )
        )

        self.acct_line.date_end = date(2023, 7, 31)
        period_date_end = date(2023, 7, 31)
        self.assertTrue(
            self.acct_line._get_generate_mis_cash_flow_forecast_line_criteria(
                period_date_end
            )
        )

        period_date_end = date(2023, 8, 31)
        self.assertFalse(
            self.acct_line._get_generate_mis_cash_flow_forecast_line_criteria(
                period_date_end
            )
        )

    def test_generate_mis_cash_flow_forecast_lines(self):
        self.acct_line.is_canceled = True
        self.acct_line._generate_mis_cash_flow_forecast_lines()
        self.acct_line.is_canceled = False
        self.acct_line.active = False
        self.acct_line._generate_mis_cash_flow_forecast_lines()

    def test_create(self):
        self.company = self.env.ref("base.main_company")

        contract_line = self.env["contract.line"].create(
            {
                "name": "Test Contract Line",
                "contract_id": self.contract.id,
                "product_id": self.env.ref("product.product_product_4").id,
                "quantity": 1,
                "price_unit": 100.0,
                "date_start": date.today(),
                "date_end": date.today() + relativedelta(months=1),
                "recurring_next_date": date.today() + relativedelta(months=1),
            }
        )
        self.assertTrue(contract_line)

        self.company.enable_contract_mis_cash_flow_forecast = False
        contract_line = self.env["contract.line"].create(
            {
                "name": "Test Contract Line",
                "contract_id": self.contract.id,
                "product_id": self.env.ref("product.product_product_4").id,
                "quantity": 1,
                "price_unit": 100.0,
                "date_start": date.today(),
                "date_end": date.today() + relativedelta(months=1),
                "recurring_next_date": date.today() + relativedelta(months=1),
            }
        )
        self.assertTrue(contract_line)
        self.assertFalse(contract_line.mis_cash_flow_forecast_line_ids)

    def test_get_mis_cash_flow_forecast_update_trigger_fields(self):
        expected_fields = [
            "name",
            "sequence",
            "product_id",
            "date_start",
            "date_end",
            "quantity",
            "price_unit",
            "discount",
            "recurring_invoicing_type",
            "recurring_next_date",
            "recurring_rule_type",
            "recurring_interval",
            "is_canceled",
            "active",
            "is_auto_renew",
        ]
        self.assertEqual(
            self.acct_line._get_mis_cash_flow_forecast_update_trigger_fields(),
            expected_fields,
        )

    def test_write(self):
        self.contract.company_id.write(
            {
                "enable_contract_mis_cash_flow_forecast": False,
            }
        )
        self.acct_line.write(
            {
                "quantity": 3,
            }
        )
        self.assertFalse(self.acct_line.mis_cash_flow_forecast_line_ids)

    def test_unlink(self):
        self.assertTrue(self.acct_line.exists())
        self.acct_line.is_canceled = True
        self.acct_line._prepare_mis_cash_flow_forecast_line(
            period_date_start=fields.Date.today(),
            period_date_end=fields.Date.today(),
            recurring_next_date=fields.Date.today(),
        )
        self.acct_line.mis_cash_flow_forecast_line_ids.unlink()
        self.acct_line.unlink()
        self.assertFalse(self.acct_line.mis_cash_flow_forecast_line_ids.exists())
        self.assertFalse(self.acct_line.exists())

    def test_cron_mis_cash_flow_generate_forecast_contract_lines(self):
        offset = 0
        self.acct_line.cron_mis_cash_flow_generate_forecast_contract_lines()
        self.acct_line.is_canceled = False
        self.assertFalse(
            self.acct_line.mis_cash_flow_forecast_line_ids,
        )
        self.acct_line.is_canceled = True
        self.assertFalse(
            self.acct_line.mis_cash_flow_forecast_line_ids,
        )
        search_result = self.acct_line.search(
            [("contract_id", "=", self.contract.id)], limit=25, offset=offset
        )
        search_result.with_delay()._generate_mis_cash_flow_forecast_lines()
        self.assertTrue(len(search_result), 1)

        search_result = self.acct_line.search(
            [("is_canceled", "=", False)], limit=25, offset=offset
        )
        search_result.with_delay()._generate_mis_cash_flow_forecast_lines()
        self.assertTrue(len(search_result), 25)

    def test_compute_mis_cash_flow_forecast_line_ids(self):
        self.acct_line._generate_mis_cash_flow_forecast_lines()
        forecast_lines = self.env["mis.cash_flow.forecast_line"].search(
            [
                ("res_model", "=", "contract.line"),
                ("res_id", "=", self.acct_line.id),
            ]
        )
        self.assertTrue(forecast_lines)
        self.assertEqual(len(forecast_lines), 12)
        self.acct_line._compute_mis_cash_flow_forecast_line_ids()
        self.assertEqual(len(self.acct_line.mis_cash_flow_forecast_line_ids), 12)
