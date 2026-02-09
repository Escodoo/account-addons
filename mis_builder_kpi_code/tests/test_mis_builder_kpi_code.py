# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import zipfile
from io import BytesIO

import xlsxwriter

from odoo.tests.common import TransactionCase


class _BaseMisBuilderSetup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_with_code = cls.env["mis.report"].create(
            {
                "name": "Relatório Teste",
                "use_code_column": True,
                "kpi_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "lucro_bruto",
                            "description": "99999 Lucro Bruto",
                            "expression": "balance",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "receita",
                            "description": "R2 Receita",
                            "expression": "balance",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            # cobre o caso "começa com dígito, mas sem espaço"
                            # (não deve quebrar nem gerar código)
                            "name": "sem_espaco",
                            "description": "1",
                            "expression": "balance",
                        },
                    ),
                ],
            }
        )
        cls.instance_with_code = cls.env["mis.report.instance"].create(
            {
                "name": "Instância Teste",
                "report_id": cls.report_with_code.id,
                "query_company_ids": [(6, 0, [cls.env.company.id])],
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
            }
        )

        cls.report_without_code = cls.env["mis.report"].create(
            {
                "name": "Relatório Teste (sem código)",
                "use_code_column": False,
                "kpi_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "lucro_bruto",
                            "description": "99999 Lucro Bruto",
                            "expression": "balance",
                        },
                    ),
                ],
            }
        )
        cls.instance_without_code = cls.env["mis.report.instance"].create(
            {
                "name": "Instância Teste (sem código)",
                "report_id": cls.report_without_code.id,
                "query_company_ids": [(6, 0, [cls.env.company.id])],
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
            }
        )

    @staticmethod
    def _xlsx_text(xlsx_bytes: bytes) -> str:
        """Extrai texto dos XMLs do XLSX para asserts simples."""
        zf = zipfile.ZipFile(BytesIO(xlsx_bytes))
        parts: list[str] = []
        for name in zf.namelist():
            if name.startswith("xl/") and name.endswith(".xml"):
                parts.append(zf.read(name).decode("utf-8", errors="ignore"))
        return "\n".join(parts)


class TestMisBuilderKpiCodeComputeAndXlsx(_BaseMisBuilderSetup):
    def _ensure_at_least_one_period(self, instance):
        """Garante pelo menos 1 período/coluna no relatório.

        O XLSX padrão do mis_builder assume que existe ao menos uma coluna;
        sem período, pode ocorrer `ValueError: max() arg is an empty sequence`.
        """
        try:
            Period = self.env["mis.report.instance.period"]
        except KeyError:
            self.skipTest("Modelo 'mis.report.instance.period' não disponível.")

        # Descobre o campo relacional (varia por versão)
        if "report_instance_id" in Period._fields:
            link_field = "report_instance_id"
        elif "instance_id" in Period._fields:
            link_field = "instance_id"
        else:
            self.skipTest(
                "Modelo 'mis.report.instance.period' sem campo de relação esperado."
            )

        if Period.search([(link_field, "=", instance.id)], limit=1):
            return

        vals = {
            link_field: instance.id,
        }
        if "name" in Period._fields:
            vals["name"] = "P1"
        if "sequence" in Period._fields:
            vals["sequence"] = 10
        if "date_from" in Period._fields:
            vals["date_from"] = instance.date_from or "2024-01-01"
        if "date_to" in Period._fields:
            vals["date_to"] = instance.date_to or "2024-12-31"

        Period.create(vals)

    def test_computed_code_extracts_only_digit_prefix_with_space(self):
        report = self.report_with_code
        assert report.computed_code(None) == ""
        assert report.computed_code("") == ""
        assert report.computed_code("R1 Lucro Bruto") == ""
        assert report.computed_code("99999 Lucro Bruto") == "99999"
        # não deve quebrar/retornar código sem separador
        assert report.computed_code("1") == ""

    def test_compute_injects_code_and_shifts_headers(self):
        result_with = self.instance_with_code.compute()
        result_without = self.instance_without_code.compute()

        # headers deslocados (+1 coluna vazia) quando use_code_column=True
        assert (
            len(result_with["header"][0]["cols"])
            == len(result_without["header"][0]["cols"]) + 1
        )
        assert (
            len(result_with["header"][1]["cols"])
            == len(result_without["header"][1]["cols"]) + 1
        )
        assert result_with["header"][0]["cols"][0]["label"] == ""
        assert result_with["header"][1]["cols"][0]["label"] == ""

        # linha com código (99999)
        row_lucro = next(
            row for row in result_with["body"] if row.get("label") == "Lucro Bruto"
        )
        assert row_lucro.get("code") == "99999"

        # linha sem código (não começa com dígito)
        row_receita = next(
            row for row in result_with["body"] if row.get("label") == "R2 Receita"
        )
        assert "code" not in row_receita

        # linha "1" (começa com dígito mas não tem espaço)
        # não deve quebrar nem virar code
        row_sem_espaco = next(
            row for row in result_with["body"] if row.get("label") == "1"
        )
        assert "code" not in row_sem_espaco

    def test_compute_without_code_column_does_not_inject_code(self):
        result = self.instance_without_code.compute()
        assert all("code" not in row for row in result["body"])

    def test_generate_xlsx_with_code_splits_code_and_label(self):
        report_obj = self.env["report.mis_builder.mis_report_instance_xlsx"]

        self._ensure_at_least_one_period(self.instance_with_code)
        stream = BytesIO()
        wb = xlsxwriter.Workbook(stream, {"in_memory": True})
        report_obj.with_context(
            active_ids=self.instance_with_code.ids
        ).generate_xlsx_report(workbook=wb, data={}, objects=self.instance_with_code)
        wb.close()

        text = self._xlsx_text(stream.getvalue())
        assert "99999" in text
        assert "Lucro Bruto" in text
        # com a coluna de código ativa, o label deve ser "Lucro Bruto" (sem prefixo)
        assert "99999 Lucro Bruto" not in text
        # KPI sem código deve manter o label original
        assert "R2 Receita" in text

    def test_generate_xlsx_without_code_keeps_prefix_in_label(self):
        report_obj = self.env["report.mis_builder.mis_report_instance_xlsx"]

        self._ensure_at_least_one_period(self.instance_without_code)
        stream = BytesIO()
        wb = xlsxwriter.Workbook(stream, {"in_memory": True})
        report_obj.with_context(
            active_ids=self.instance_without_code.ids
        ).generate_xlsx_report(workbook=wb, data={}, objects=self.instance_without_code)
        wb.close()

        text = self._xlsx_text(stream.getvalue())
        # sem a coluna de código, o label deve manter o prefixo
        assert "99999 Lucro Bruto" in text
