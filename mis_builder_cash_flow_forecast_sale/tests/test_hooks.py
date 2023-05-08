# Copyright 2023 - TODAY Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHooks(TransactionCase):
    def setUp(self):
        super(TestHooks, self).setUp()
        self.env = self.env(user=self.env.ref("base.user_admin"))
        self.sale_order = self.env["sale.order"].search(
            [("state", "in", ["sale", "done"])]
        )

    def test_post_init_hook(self):
        self.assertTrue(self.sale_order)
        self.sale_order._compute_forecast_uninvoiced_amount()
