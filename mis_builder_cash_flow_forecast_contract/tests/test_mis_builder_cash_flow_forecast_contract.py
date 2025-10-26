# Copyright 2025 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestMisBuilderCashFlowForecastContract(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Setup company with forecast enabled
        cls.company = cls.env.ref("base.main_company")
        cls.company.write(
            {
                "enable_contract_mis_cash_flow_forecast": True,
                "contract_mis_cash_flow_forecast_interval": 12,
                "contract_mis_cash_flow_forecast_rule_type": "monthly",
            }
        )

        # Create partner
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "company_id": cls.company.id,
            }
        )

        # Create product
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Service",
                "type": "service",
                "list_price": 100.0,
            }
        )

        # Create contract
        cls.contract = cls.env["contract.contract"].create(
            {
                "name": "Test Contract",
                "partner_id": cls.partner.id,
                "company_id": cls.company.id,
                "contract_type": "sale",
            }
        )

        # Create contract line
        cls.contract_line = cls.env["contract.line"].create(
            {
                "contract_id": cls.contract.id,
                "product_id": cls.product.id,
                "name": "Test Contract Line",
                "quantity": 1,
                "price_unit": 100.0,
                "discount": 0.0,
                "date_start": fields.Date.today(),
                "date_end": fields.Date.today() + relativedelta(years=1),
                "recurring_rule_type": "monthly",
                "recurring_interval": 1,
                "recurring_invoicing_type": "pre-paid",
            }
        )

    def test_compute_forecast_line_count(self):
        """Test that forecast line count is computed correctly."""
        self.contract_line._generate_mis_cash_flow_forecast_lines()
        self.assertGreater(
            self.contract_line.mis_cash_flow_forecast_line_count,
            0,
            "Forecast line count should be greater than 0",
        )

    def test_generate_forecast_lines(self):
        """Test generation of forecast lines."""
        self.contract_line._generate_mis_cash_flow_forecast_lines()

        forecast_lines = self.env["mis.cash_flow.forecast_line"].search(
            [
                ("res_model", "=", "contract.line"),
                ("res_id", "=", self.contract_line.id),
            ]
        )

        self.assertTrue(
            forecast_lines,
            "Forecast lines should be generated",
        )
        self.assertGreater(
            len(forecast_lines),
            0,
            "At least one forecast line should be created",
        )

    def test_forecast_line_values(self):
        """Test that forecast line values are correct."""
        self.contract_line._generate_mis_cash_flow_forecast_lines()

        forecast_lines = self.env["mis.cash_flow.forecast_line"].search(
            [
                ("res_model", "=", "contract.line"),
                ("res_id", "=", self.contract_line.id),
            ]
        )

        first_forecast = forecast_lines[0]

        self.assertEqual(
            first_forecast.partner_id,
            self.partner,
            "Partner should match contract partner",
        )
        self.assertEqual(
            first_forecast.company_id,
            self.company,
            "Company should match contract company",
        )
        self.assertEqual(
            first_forecast.balance,
            100.0,
            "Balance should match contract line price",
        )

    def test_forecast_regeneration_on_write(self):
        """Test that forecast lines are regenerated on contract line update."""
        self.contract_line._generate_mis_cash_flow_forecast_lines()

        # Update price_unit (trigger field)
        self.contract_line.write({"price_unit": 150.0})

        # Forecast lines should be regenerated
        forecast_lines = self.env["mis.cash_flow.forecast_line"].search(
            [
                ("res_model", "=", "contract.line"),
                ("res_id", "=", self.contract_line.id),
            ]
        )

        self.assertTrue(
            forecast_lines,
            "Forecast lines should still exist after update",
        )

    def test_forecast_deletion_on_unlink(self):
        """Test that forecast lines are deleted when contract line is deleted."""
        self.contract_line._generate_mis_cash_flow_forecast_lines()

        forecast_lines = self.env["mis.cash_flow.forecast_line"].search(
            [
                ("res_model", "=", "contract.line"),
                ("res_id", "=", self.contract_line.id),
            ]
        )

        self.assertTrue(
            forecast_lines,
            "Forecast lines should exist before deletion",
        )

        line_id = self.contract_line.id

        # Cancel the contract line before unlinking (required by contract module)
        self.contract_line.cancel()
        self.contract_line.unlink()

        remaining_forecasts = self.env["mis.cash_flow.forecast_line"].search(
            [
                ("res_model", "=", "contract.line"),
                ("res_id", "=", line_id),
            ]
        )

        self.assertFalse(
            remaining_forecasts,
            "Forecast lines should be deleted with contract line",
        )

    def test_forecast_with_discount(self):
        """Test forecast generation with discount applied."""
        line_with_discount = self.env["contract.line"].create(
            {
                "contract_id": self.contract.id,
                "product_id": self.product.id,
                "name": "Test Contract Line with Discount",
                "quantity": 1,
                "price_unit": 100.0,
                "discount": 10.0,
                "date_start": fields.Date.today(),
                "date_end": fields.Date.today() + relativedelta(months=6),
                "recurring_rule_type": "monthly",
                "recurring_interval": 1,
                "recurring_invoicing_type": "pre-paid",
            }
        )

        line_with_discount._generate_mis_cash_flow_forecast_lines()

        forecast_lines = self.env["mis.cash_flow.forecast_line"].search(
            [
                ("res_model", "=", "contract.line"),
                ("res_id", "=", line_with_discount.id),
            ]
        )

        self.assertTrue(forecast_lines, "Forecast lines should be generated")

        # Check that discount is applied (100 * 0.9 = 90)
        first_forecast = forecast_lines[0]
        self.assertEqual(
            first_forecast.balance,
            90.0,
            "Balance should reflect 10% discount",
        )

    def test_forecast_disabled_company(self):
        """Test that forecast is not generated when disabled at company level."""
        self.company.enable_contract_mis_cash_flow_forecast = False

        line_disabled = self.env["contract.line"].create(
            {
                "contract_id": self.contract.id,
                "product_id": self.product.id,
                "name": "Test Contract Line - Disabled",
                "quantity": 1,
                "price_unit": 100.0,
                "date_start": fields.Date.today(),
                "date_end": fields.Date.today() + relativedelta(months=3),
                "recurring_rule_type": "monthly",
                "recurring_interval": 1,
                "recurring_invoicing_type": "pre-paid",
            }
        )

        line_disabled._generate_mis_cash_flow_forecast_lines()

        forecast_lines = self.env["mis.cash_flow.forecast_line"].search(
            [
                ("res_model", "=", "contract.line"),
                ("res_id", "=", line_disabled.id),
            ]
        )

        self.assertFalse(
            forecast_lines,
            "No forecast lines should be generated when feature is disabled",
        )

        # Restore company setting
        self.company.enable_contract_mis_cash_flow_forecast = True

    def test_forecast_canceled_line(self):
        """Test that forecast is not generated for canceled contract lines."""
        canceled_line = self.env["contract.line"].create(
            {
                "contract_id": self.contract.id,
                "product_id": self.product.id,
                "name": "Test Contract Line - Canceled",
                "quantity": 1,
                "price_unit": 100.0,
                "date_start": fields.Date.today(),
                "date_end": fields.Date.today() + relativedelta(months=3),
                "recurring_rule_type": "monthly",
                "recurring_interval": 1,
                "recurring_invoicing_type": "pre-paid",
                "is_canceled": True,
            }
        )

        canceled_line._generate_mis_cash_flow_forecast_lines()

        forecast_lines = self.env["mis.cash_flow.forecast_line"].search(
            [
                ("res_model", "=", "contract.line"),
                ("res_id", "=", canceled_line.id),
            ]
        )

        self.assertFalse(
            forecast_lines,
            "No forecast lines should be generated for canceled lines",
        )

    def test_forecast_end_date_calculation(self):
        """Test that forecast end date is calculated correctly."""
        end_date = self.contract_line._get_mis_cash_flow_contract_forecast_end_date()

        today = fields.Date.context_today(self.contract_line)
        expected_end_date = today + relativedelta(months=12)

        self.assertEqual(
            end_date,
            expected_end_date,
            "Forecast end date should be 12 months from today",
        )

    def test_action_show_mis_forecast(self):
        """Test the action to show MIS forecast."""
        self.contract_line._generate_mis_cash_flow_forecast_lines()

        action = self.contract.action_show_mis_forecast()

        self.assertEqual(
            action["type"],
            "ir.actions.act_window",
            "Action should be a window action",
        )
        self.assertEqual(
            action["res_model"],
            "mis.cash_flow.forecast_line",
            "Action should open forecast line model",
        )
        self.assertIn(
            "domain",
            action,
            "Action should have domain filter",
        )

    def test_prepare_forecast_line_values(self):
        """Test preparation of forecast line values."""
        period_start = fields.Date.today()
        period_end = period_start + relativedelta(months=1)
        recurring_next = period_start

        values = self.contract_line._prepare_mis_cash_flow_forecast_line(
            period_start,
            period_end,
            recurring_next,
        )

        self.assertIn("name", values, "Values should contain name")
        self.assertIn("date", values, "Values should contain date")
        self.assertIn("account_id", values, "Values should contain account_id")
        self.assertIn("partner_id", values, "Values should contain partner_id")
        self.assertIn("balance", values, "Values should contain balance")
        self.assertIn("company_id", values, "Values should contain company_id")
        self.assertIn("res_model_id", values, "Values should contain res_model_id")
        self.assertIn("res_id", values, "Values should contain res_id")

        self.assertEqual(
            values["partner_id"],
            self.partner.id,
            "Partner ID should match",
        )
        self.assertEqual(
            values["company_id"],
            self.company.id,
            "Company ID should match",
        )

    def test_cron_generate_forecast_lines(self):
        """Test cron job for generating forecast lines."""
        # Create multiple contract lines
        test_lines = []
        for i in range(3):
            line = self.env["contract.line"].create(
                {
                    "contract_id": self.contract.id,
                    "product_id": self.product.id,
                    "name": f"Test Contract Line {i}",
                    "quantity": 1,
                    "price_unit": 100.0,
                    "date_start": fields.Date.today(),
                    "date_end": fields.Date.today() + relativedelta(months=3),
                    "recurring_rule_type": "monthly",
                    "recurring_interval": 1,
                    "recurring_invoicing_type": "pre-paid",
                }
            )
            test_lines.append(line)

        # Run cron job
        # Note: In test environment, we call the generation method directly
        # as the queue_job with_delay() may not execute immediately
        contract_lines = (
            self.env["contract.line"]
            .search(
                [
                    ("is_canceled", "=", False),
                    ("id", "in", [line.id for line in test_lines]),
                ]
            )
            .filtered(lambda x: x.create_invoice_visibility)
        )

        # Generate forecast lines directly without queue_job
        for line in contract_lines:
            line._generate_mis_cash_flow_forecast_lines()

        # Check that forecast lines were created
        all_forecast_lines = self.env["mis.cash_flow.forecast_line"].search(
            [
                ("res_model", "=", "contract.line"),
                ("res_id", "in", [line.id for line in test_lines]),
            ]
        )

        self.assertTrue(
            all_forecast_lines,
            "Cron should generate forecast lines",
        )
