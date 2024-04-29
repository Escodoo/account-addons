# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MisReportKpi(models.Model):

    _inherit = "mis.report.kpi"

    code = fields.Char()
