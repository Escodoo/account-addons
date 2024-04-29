# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class MisReportInstance(models.Model):

    _inherit = "mis.report.instance"

    def compute(self):
        self.ensure_one()
        kpi_matrix = self._compute_matrix()
        kpi_matrix_dict = kpi_matrix.as_dict()

        empty_col = [{"label": "", "description": "", "colspan": 1}]
        kpi_matrix_dict["header"][0]["cols"] = (
            empty_col + kpi_matrix_dict["header"][0]["cols"]
        )
        kpi_matrix_dict["header"][1]["cols"] = (
            empty_col + kpi_matrix_dict["header"][1]["cols"]
        )

        for idx, row in enumerate(kpi_matrix_dict["body"]):
            code = self.report_id.kpi_ids.filtered(
                lambda k: k.name == row["row_id"]
            ).code
            kpi_matrix_dict["body"][idx].update({"code": code})

        return kpi_matrix_dict
