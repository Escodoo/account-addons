# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMisCashFlowForecastLine(TransactionCase):
    def setUp(self):
        super(TestMisCashFlowForecastLine, self).setUp()
        self.model_test = self.env["ir.model"].create(
            {
                "name": "Test Model",
                "model": "x_test.model",
            }
        )
        self.env["ir.model.data"].create(
            {
                "name": "test.model_test",
                "module": "test",
                "model": "ir.model",
                "res_id": self.model_test.id,
            }
        )
        self.account_move = self.env["account.move"].create(
            {
                "name": "Test Account Move",
                "ref": "Test Reference",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test Journal Item",
                            "account_id": self.env.ref(
                                "account.data_account_type_receivable"
                            ).id,
                            "debit": 100.00,
                            "credit": 0.00,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Test Journal Item",
                            "account_id": self.env.ref(
                                "account.data_account_type_revenue"
                            ).id,
                            "debit": 0.00,
                            "credit": 100.00,
                        },
                    ),
                ],
            }
        )
        self.current_date = datetime.today()
        self.account = self.env["account.account"].create(
            {
                "name": "Test Account",
                "code": "TEST",
                "user_type_id": self.env.ref("account.data_account_type_revenue").id,
            }
        )
        self.company = self.env.ref("base.main_company")
        self.forecast_line = self.env["mis.cash_flow.forecast_line"].create(
            {
                "name": "Test",
                "company_id": self.company.id,
                "date": self.current_date,
                "account_id": self.account.id,
                "balance": 42,
            }
        )

    def test_action_open_document_related(self):
        self.forecast_line.res_model = "x_test.model"
        self.forecast_line.res_id = 1
        action = self.forecast_line.action_open_document_related()
        self.assertTrue(
            action["res_model"] == "x_test.model" and action["res_id"] == 1,
            msg="Should return a valid action with res_model = 'x_test.model' and res_id = '1'",
        )
        self.forecast_line.res_model = False
        self.forecast_line.res_id = False
        self.assertFalse(
            self.forecast_line.action_open_document_related(),
            msg="Should return False when res_model and res_id are False",
        )

    def test_action_open_parent_document_related(self):
        forecast_line_parent = self.env["mis.cash_flow.forecast_line"].create(
            {
                "name": "Test",
                "company_id": self.company.id,
                "date": self.current_date,
                "account_id": self.account.id,
                "balance": 42,
                "res_model_id": self.account_move.id,
            }
        )
        self.assertFalse(forecast_line_parent.action_open_parent_document_related())
        forecast_line_parent.parent_res_model = self.account_move._name
        forecast_line_parent.parent_res_id = self.account_move.id
        self.assertTrue(forecast_line_parent.action_open_parent_document_related())
