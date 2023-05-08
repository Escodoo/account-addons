# Copyright (C) 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):

    env = api.Environment(cr, SUPERUSER_ID, {})
    orders = env["sale.order"].search([("state", "in", ["sale", "done"])])
    if orders:
        orders.sudo()._compute_forecast_uninvoiced_amount()
