# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MisReportInstance(models.Model):

    _inherit = "mis.report.instance"

    is_round_numbers = fields.Boolean(default=False)
    hide_period_labels = fields.Boolean(default=False)
