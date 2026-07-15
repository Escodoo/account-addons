# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    production_date = fields.Date(copy=False)

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        for move in self:
            if move.production_date:
                move.line_ids.analytic_line_ids.write({"date": move.production_date})
        return res
