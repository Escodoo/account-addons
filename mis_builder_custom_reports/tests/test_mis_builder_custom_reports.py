# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMisBuilderCustomReports(TransactionCase):
    def test_kpimatrixrow_label_profit_loss_and_date_to(self):
        class DummyMatrix:
            @staticmethod
            def get_account_name(account_id):
                return f"Conta Lucro $date_to (id={account_id})"

        class DummyKpi:
            def __init__(self, description, is_profit_loss):
                self.description = description
                self.is_profit_loss = is_profit_loss

        from odoo.addons.mis_builder.models.kpimatrix import KpiMatrixRow

        row = KpiMatrixRow.__new__(KpiMatrixRow)
        row._matrix = DummyMatrix()
        row.account_id = None
        row.kpi = DummyKpi("LUCRO até $date_to", True)
        row.sum_row = lambda: -1
        row.compute_date_to = lambda: "31/12/2024"
        self.assertEqual(row.label, "PREJUÍZO até $date_to")

        row2 = KpiMatrixRow.__new__(KpiMatrixRow)
        row2._matrix = DummyMatrix()
        row2.account_id = None
        row2.kpi = DummyKpi("Prejuízo em $date_to", True)
        row2.sum_row = lambda: 1
        row2.compute_date_to = lambda: "31/12/2024"
        self.assertEqual(row2.label, "Lucro em $date_to")

        row3 = KpiMatrixRow.__new__(KpiMatrixRow)
        row3._matrix = DummyMatrix()
        row3.account_id = 10
        row3.kpi = DummyKpi("IGNORADO", True)
        row3.sum_row = lambda: -5
        row3.compute_date_to = lambda: "01/01/2025"
        self.assertEqual(row3.label, "Conta Prejuízo $date_to (id=10)")

    def test_fields_exist(self):
        model = self.env["mis.report.instance"]
        self.assertIn("is_round_numbers", model._fields)
        self.assertIn("hide_period_labels", model._fields)

    def test_form_view_injects_fields(self):
        view = self.env.ref("mis_builder_custom_reports.mis_report_instance_view_form")
        arch = view.with_context(lang="en_US").arch_db
        self.assertIn('name="is_round_numbers"', arch)
        self.assertIn('name="hide_period_labels"', arch)

    def test_qweb_inherited_template_present(self):
        view = self.env.ref("mis_builder_custom_reports.report_mis_report_instance")
        arch = view.with_context(lang="en_US").arch_db
        self.assertIn("mis_footer_line", arch)
        self.assertIn("o_standard_footer", arch)

    def test_qweb_render_hide_period_labels(self):
        company = self.env.ref("base.main_company")
        partner_model_id = self.env.ref("base.model_res_partner").id
        partner_create_date_field_id = self.env.ref(
            "base.field_res_partner__create_date"
        ).id
        partner_debit_field_id = self.env.ref("account.field_res_partner__debit").id

        report = self.env["mis.report"].create(
            {
                "name": "test report (custom reports)",
                "subkpi_ids": [
                    (0, 0, {"name": "sk1", "description": "subkpi 1", "sequence": 1})
                ],
                "query_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "partner",
                            "model_id": partner_model_id,
                            "field_ids": [(4, partner_debit_field_id, None)],
                            "date_field": partner_create_date_field_id,
                            "aggregate": "sum",
                        },
                    )
                ],
            }
        )

        self.env["mis.report.kpi"].create(
            {
                "report_id": report.id,
                "description": "kpi 1",
                "name": "k1",
                "multi": True,
                "expression_ids": [
                    (
                        0,
                        0,
                        {"name": "bale[200%]", "subkpi_id": report.subkpi_ids[0].id},
                    ),
                ],
            }
        )

        period_label = "PL_HIDE_ME_123"
        instance = self.env["mis.report.instance"].create(
            {
                "name": "test instance (custom reports)",
                "report_id": report.id,
                "company_id": company.id,
                "period_ids": [
                    (
                        0,
                        0,
                        {
                            "name": period_label,
                            "mode": "fix",
                            "manual_date_from": "2024-01-01",
                            "manual_date_to": "2024-12-31",
                            "subkpi_ids": [(4, report.subkpi_ids[0].id, None)],
                        },
                    )
                ],
            }
        )
        html, _ = self.env["ir.actions.report"]._render_qweb_html(
            "mis_builder.report_mis_report_instance",
            [instance.id],
        )
        html_s = str(html)
        self.assertIn(period_label, html_s)
        instance.hide_period_labels = True
        html2, _ = self.env["ir.actions.report"]._render_qweb_html(
            "mis_builder.report_mis_report_instance",
            [instance.id],
        )
        html2_s = str(html2)
        self.assertNotIn(period_label, html2_s)
