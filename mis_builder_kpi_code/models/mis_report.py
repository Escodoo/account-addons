# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MisReportKpi(models.Model):

    _inherit = "mis.report.kpi"

    code = fields.Char()
    use_code_column = fields.Boolean(related="report_id.use_code_column")


class MisReport(models.Model):

    _inherit = "mis.report"

    use_code_column = fields.Boolean(default=False)

    def computed_code(self, description):
        code = ""
        if description:
            first_character = description[0]
            if first_character.isdigit():
                code = description.split(" ")[0]
        return code
