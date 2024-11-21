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


@property
def custom_label(self):
    label = self.kpi.description
    if self.account_id:
        label = self._matrix.get_account_name(self.account_id)

    if self.sum_row() < 0 and self.kpi.is_profit_loss:
        return label.replace("Lucro", "Prejuízo")
    return label


KpiMatrixRow.sum_row = sum_row
KpiMatrixRow.label = custom_label
