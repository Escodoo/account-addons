# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    use_code_column = fields.Boolean(related="report_id.use_code_column")

    def compute(self):
        self.ensure_one()
        if not self.use_code_column:
            return super().compute()
        else:
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
                label = row["label"]
                code = self.report_id.computed_code(label)
                if code:
                    label = label.split(" ", 1)[1]
                    kpi_matrix_dict["body"][idx].update(
                        {
                            "code": code,
                            "label": label,
                        }
                    )

            return kpi_matrix_dict
