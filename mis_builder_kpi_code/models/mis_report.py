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
        """Extrai o código inicial do KPI a partir do texto.

        Regras:
        - Só considera "código" quando o primeiro caractere é um dígito
        - Exige um espaço para separar código e descrição, evitando erros
          em casos como "1" ou "1ABC" sem separador.
        """
        if not isinstance(description, str) or not description:
            return ""

        if description[0].isdigit() and " " in description:
            return description.split(" ", 1)[0]

        return ""
