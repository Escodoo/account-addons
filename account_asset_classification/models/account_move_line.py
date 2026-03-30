# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    asset_classification = fields.Selection(
        [
            ("entry", "Entry"),
            ("depression", "Depression"),
            ("reclassification", "Reclassification"),
        ],
        default=False,
    )
