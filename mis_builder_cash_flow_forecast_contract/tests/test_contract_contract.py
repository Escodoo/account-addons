# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestContractContract(TransactionCase):
    def setUp(self):
        super(TestContractContract, self).setUp()
        self.company = self.env.ref("base.main_company")
        self.contract = self.env["contract.contract"].create(
            {
                "name": "Test Contract",
                "partner_id": self.env.ref("base.res_partner_1").id,
                "company_id": self.company.id,
            }
        )
        self.product = self.env["product.product"].create(
            {
                "name": "Produto de Teste",
                "list_price": 100.0,
            }
        )
        self.contract_line = self.env["contract.line"].create(
            {
                "name": "Contract Line",
                "contract_id": self.contract.id,
                "product_id": self.product.id,
                "price_unit": 50.0,
                "quantity": 2,
            }
        )

    def test_get_mis_cash_flow_forecast_update_trigger_fields(self):
        expected_fields = [
            "partner_id",
            "pricelist_id",
            "fiscal_position_id",
            "currency_id",
            "contract_line_ids",
        ]
        self.assertEqual(
            self.contract._get_mis_cash_flow_forecast_update_trigger_fields(),
            expected_fields,
        )

    def test_action_show_mis_forecast(self):
        self.contract_line.write({"price_unit": 60.0})
        self.contract.write({"date_start": fields.Date.today()})
        action = self.contract.action_show_mis_forecast()
        self.assertEqual(action["name"], _("Cash Flow Forecast - Contract"))
        self.assertEqual(action["res_model"], "mis.cash_flow.forecast_line")
        self.assertTrue(action["domain"])
        self.assertEqual(len(action["domain"]), 2)
        self.assertEqual(
            action["domain"][0], ("parent_res_model", "=", "contract.contract")
        )
        self.assertEqual(action["domain"][1], ("parent_res_id", "=", self.contract.id))
        self.assertIn("pivot", action["view_mode"])
        self.assertIn("tree", action["view_mode"])

    def test_unlink(self):
        self.contract_line._prepare_mis_cash_flow_forecast_line(
            period_date_start=fields.Date.today(),
            period_date_end=fields.Date.today(),
            recurring_next_date=fields.Date.today(),
        )
        self.contract_line.mis_cash_flow_forecast_line_ids.unlink()
        self.contract.unlink()
        self.assertFalse(self.contract.exists())
        self.assertFalse(self.contract.contract_line_ids.exists())
        self.assertFalse(
            self.contract.contract_line_ids.mis_cash_flow_forecast_line_ids.exists()
        )

    def test_write(self):
        self.contract._get_mis_cash_flow_forecast_update_trigger_fields()
        self.contract.company_id.enable_contract_mis_cash_flow_forecast = False
        self.contract.write({"name": "New Contract Name"})
        self.assertFalse(
            self.contract.company_id.enable_contract_mis_cash_flow_forecast
        )
        forecast_lines = self.contract_line.search(
            [("contract_id", "=", self.contract.id)]
        ).mapped("mis_cash_flow_forecast_line_ids")
        self.assertFalse(forecast_lines)
        self.contract.company_id.enable_contract_mis_cash_flow_forecast = True
        self.assertTrue(self.contract.company_id.enable_contract_mis_cash_flow_forecast)
