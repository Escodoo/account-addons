# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_IN


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("product_id", "partner_id", "move_id.fiscal_operation_type")
    def _compute_product_fiscal_fields(self):
        for line in self:
            if line.product_id and line.move_id.fiscal_operation_type == FISCAL_IN:
                partner_service_type = (
                    line.partner_id.partner_service_type_ids.filtered(
                        lambda x, product=line.product_id: x.product_id == product
                    )[:1]
                )
                line.service_type_id = (
                    partner_service_type.service_type_id
                    if partner_service_type
                    else line.product_id.service_type_id
                )
