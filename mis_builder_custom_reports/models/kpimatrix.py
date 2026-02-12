# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.mis_builder.models.kpimatrix import KpiMatrixRow


def sum_row(self):
    cells = self.iter_cells()
    total = 0
    for cell in cells:
        if cell and cell.val not in (None, "AccountingNone"):
            total += float(cell.val or 0)
    return total


def compute_date_to(self):
    report_id = self.kpi.report_id
    report_instance = report_id.env["mis.report.instance"].search(
        [
            ("report_id", "=", report_id.id),
        ]
    )
    if len(report_instance) == 1 and report_instance.date_to:
        date = str(report_instance.date_to)
        return "/".join(reversed(date.split("-")))
    else:
        return ""


@property
def custom_label(self):
    label = self.kpi.description
    if self.account_id:
        label = self._matrix.get_account_name(self.account_id)

    if self.kpi.is_profit_loss:
        if self.sum_row() < 0:
            return label.replace("Lucro", "Prejuízo").replace("LUCRO", "PREJUÍZO")
        elif self.sum_row() > 0:
            return label.replace("Prejuízo", "Lucro").replace("PREJUÍZO", "LUCRO")

    return label.replace("$date_to", self.compute_date_to())


KpiMatrixRow.sum_row = sum_row
KpiMatrixRow.compute_date_to = compute_date_to
KpiMatrixRow.label = custom_label
