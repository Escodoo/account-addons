# Copyright 2023 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    def action_post(self):
        res = super().action_post()
        for sale_order in self:
            order = sale_order.order_line.mapped("blanket_order_line.order_id")
            if (
                order
                and order.company_id.enable_sale_blanket_order_mis_cash_flow_forecast
            ):
                order.with_delay()._generate_mis_cash_flow_forecast_lines()
        return res

    def button_cancel(self):
        super().button_cancel()
        for sale_order in self:
            order = sale_order.order_line.mapped("blanket_order_line.order_id")
            if (
                order
                and order.company_id.enable_sale_blanket_order_mis_cash_flow_forecast
            ):
                order._compute_forecast_uninvoiced_amount()
                order.with_delay()._generate_mis_cash_flow_forecast_lines()

    def button_draft(self):
        super().button_draft()
        for sale_order in self:
            order = sale_order.order_line.mapped("blanket_order_line.order_id")
            if (
                order
                and order.company_id.enable_sale_blanket_order_mis_cash_flow_forecast
            ):
                order._compute_forecast_uninvoiced_amount()
                order.with_delay()._generate_mis_cash_flow_forecast_lines()

    @api.model
    def create(self, vals_list):
        sale_orders = super().create(vals_list)
        for sale_order in sale_orders:
            order = sale_order.order_line.mapped("blanket_order_line.order_id")
            if (
                order
                and order.company_id.enable_sale_blanket_order_mis_cash_flow_forecast
            ):
                order._compute_forecast_uninvoiced_amount()
                order.with_delay()._generate_mis_cash_flow_forecast_lines()
        return sale_orders
