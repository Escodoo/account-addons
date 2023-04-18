# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPostInitHook(TransactionCase):
    def setUp(self):
        super(TestPostInitHook, self).setUp()
        self.order_vals = {
            "partner_id": self.env.ref("base.res_partner_2").id,
            "currency_id": self.env.ref("base.USD").id,
            "company_id": self.env.ref("base.main_company").id,
        }
        self.order = self.env["purchase.order"].create(self.order_vals)

    def test_action_post_init_hook(self):
        self.order.state = "purchase"
        orders = self.env["purchase.order"].search(
            [("state", "in", ["purchase", "done"])]
        )
        self.order._compute_forecast_uninvoiced_amount()
        self.assertEqual(self.order.state, orders[0].state)
