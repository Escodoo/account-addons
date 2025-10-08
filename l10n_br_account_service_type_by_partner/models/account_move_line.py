# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_IN


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("product_id", "partner_id", "move_id.fiscal_operation_type")
    def _compute_product_fiscal_fields(self):
        if self._context.get("skip_compute_product_fiscal_fields"):
            return
        res = super()._compute_product_fiscal_fields()
        if self.product_id and self.move_id.fiscal_operation_type == FISCAL_IN:
            partner_service_type = self.partner_id.partner_service_type_ids.filtered(
                lambda x: x.product_id == self.product_id
            )
            if partner_service_type:
                self.service_type_id = partner_service_type.service_type_id
            else:
                self.service_type_id = self.product_id.service_type_id
        return res
