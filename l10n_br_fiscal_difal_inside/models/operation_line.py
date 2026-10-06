# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class OperationLine(models.Model):
    _inherit = "l10n_br_fiscal.operation.line"

    difal_inside_basis = fields.Boolean(string="DIFAL Inside Basis")
