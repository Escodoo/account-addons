# Copyright 2024 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.mis_builder.models.accounting_none import AccountingNone
from odoo.addons.mis_builder.models.kpimatrix import KpiMatrixRow


def sum_row(self):
    cells = self.iter_cells()
    total = 0
    for cell in cells:
        if (
            cell
            and cell.val is not None
            and not isinstance(cell.val, type(AccountingNone))
        ):
            try:
                total += float(cell.val or 0)
            except (ValueError, TypeError):
                continue
    return total


def compute_date_to(self):
    kpi = getattr(self, "kpi", None)
    if not kpi or not kpi.report_id:
        return ""
    report_id = kpi.report_id
    report_instance = report_id.env["mis.report.instance"].search(
        [
            ("report_id", "=", report_id.id),
        ],
        limit=1,
    )
    if report_instance and report_instance.date_to:
        date = str(report_instance.date_to)
        return "/".join(reversed(date.split("-")))
    else:
        return ""


@property
def custom_label(self):
    kpi = getattr(self, "kpi", None)
    if not kpi:
        return ""
    label = kpi.description or ""
    if getattr(self, "account_id", None):
        label = self._matrix.get_account_name(self.account_id)

    if getattr(kpi, "is_profit_loss", False):
        row_sum = self.sum_row()
        if row_sum < 0:
            return label.replace("Lucro", "Prejuízo").replace("LUCRO", "PREJUÍZO")
        elif row_sum > 0:
            return label.replace("Prejuízo", "Lucro").replace("PREJUÍZO", "LUCRO")
        return label

    date_to = self.compute_date_to()
    return label.replace("$date_to", date_to)


KpiMatrixRow.sum_row = sum_row
KpiMatrixRow.compute_date_to = compute_date_to
KpiMatrixRow.label = custom_label
