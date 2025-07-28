# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from io import BytesIO
from unittest.mock import patch

import xlsxwriter

from odoo.tests.common import TransactionCase


class _BaseMisBuilderSetup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report = cls.env["mis.report"].create(
            {
                "name": "Relatório Teste",
                "use_code_column": True,
                "kpi_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "lucro_bruto",
                            "description": "R1 Lucro Bruto",
                            "expression": "balance",
                        },
                    )
                ],
            }
        )
        cls.instance = cls.env["mis.report.instance"].create(
            {
                "name": "Instância Teste",
                "report_id": cls.report.id,
                "query_company_ids": [(6, 0, [cls.env.company.id])],
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
            }
        )

    def _fake_computed_code(self, label: str):
        return "R1" if isinstance(label, str) and label.startswith("R1 ") else False


class TestMisBuilderKpiCodeComputeAndXlsx(_BaseMisBuilderSetup):
    def test_compute_injects_code_and_shifts_headers(self):
        with patch.object(type(self.report), "computed_code", autospec=True) as m_code:
            m_code.side_effect = lambda _self, label: self._fake_computed_code(label)
            result = self.instance.compute()
        assert result["header"][0]["cols"][0]["label"] == ""
        assert result["header"][1]["cols"][0]["label"] == ""
        body0 = result["body"][0]
        assert body0.get("code") == "R1"
        assert body0.get("label", "").startswith("Lucro Bruto")
        assert not body0.get("label", "").startswith("R1 ")

    def test_generate_xlsx_calls_computed_code_and_runs(self):
        report_obj = self.env["report.mis_builder.mis_report_instance_xlsx"]

        with patch.object(type(self.report), "computed_code", autospec=True) as m_code:
            m_code.side_effect = lambda _self, label: self._fake_computed_code(label)

            stream = BytesIO()
            wb = xlsxwriter.Workbook(stream, {"in_memory": True})
            report_obj.with_context(active_ids=self.instance.ids).generate_xlsx_report(
                workbook=wb, data={}, objects=self.instance
            )
            wb.close()
            assert (
                m_code.call_count > 0
            ), "computed_code() não foi chamado durante o XLSX"
