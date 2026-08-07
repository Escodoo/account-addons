# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import SavepointCase
from odoo.tests.common import Form


class TestDifalInside(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.partner = cls.env.ref("l10n_br_base.res_partner_cliente5_pe")
        cls.partner.ind_ie_dest = "9"
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.product = cls.env.ref("product.product_product_6")

        cls.fcp_tax_definition = cls.env["l10n_br_fiscal.tax.definition"].create(
            {
                "icms_regulation_id": cls.company.icms_regulation_id.id,
                "state_from_id": cls.env.ref("base.state_br_pe").id,
                "state_to_ids": [(6, 0, [cls.env.ref("base.state_br_pe").id])],
                "is_taxed": True,
                "is_debit_credit": False,
                "custom_tax": True,
                "tax_id": cls.env.ref("l10n_br_fiscal.tax_icmsfcp_1").id,
                "tax_group_id": cls.env.ref("l10n_br_fiscal.tax_group_icmsfcp").id,
                "state": "approved",
            }
        )

    def _create_document_line(self, price_unit):
        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
            )
        )
        doc_form.company_id = self.company
        doc_form.partner_id = self.partner
        doc_form.fiscal_operation_id = self.fiscal_operation

        with doc_form.fiscal_line_ids.new() as line_form:
            line_form.product_id = self.product
            line_form.price_unit = price_unit
            line_form.quantity = 1.0

        doc = doc_form.save()
        return doc.fiscal_line_ids[0]

    def _enable_inside_mode(self):
        self.fiscal_operation.line_ids.write({"difal_inside_basis": True})

    def test_difal_inside(self):
        """Create a document using a fiscal operation with inside mode enabled."""
        self.product.icms_origin = "1"
        self._enable_inside_mode()

        line = self._create_document_line(22226.15)

        self.assertEqual(line.icms_origin_percent, 4.0)
        self.assertEqual(line.icms_destination_percent, 20.5)
        self.assertEqual(line.icms_destination_base, 28313.57)
        self.assertEqual(line.icms_destination_value, 4671.74)
        self.assertEqual(line.icmsfcp_percent, 1.0)
        self.assertEqual(line.icmsfcp_base, 28313.57)
        self.assertEqual(line.icmsfcp_value, 283.14)

    def test_difal_inside_fcp_computed_before_icms(self):
        """The FCP base follows the grossed up base whatever the tax order.

        When the ICMS FCP tax group is set to be computed before the ICMS one,
        the core cannot copy the DIFAL base into the FCP base.
        """
        self.product.icms_origin = "1"
        self._enable_inside_mode()
        self.env.ref("l10n_br_fiscal.tax_group_icmsfcp").compute_sequence = 10

        line = self._create_document_line(22226.15)

        self.assertEqual(line.icms_destination_base, 28313.57)
        self.assertEqual(line.icmsfcp_base, 28313.57)
        self.assertEqual(line.icmsfcp_value, 283.14)

    def test_difal_inside_without_fcp(self):
        """Without an FCP rate the base is grossed up by the ICMS only."""
        fcp_definitions = self.env["l10n_br_fiscal.tax.definition"].search(
            [
                (
                    "tax_group_id",
                    "=",
                    self.env.ref("l10n_br_fiscal.tax_group_icmsfcp").id,
                ),
                ("state_to_ids", "in", self.env.ref("base.state_br_pe").id),
            ]
        )
        fcp_definitions.write({"state": "draft"})
        fcp_definitions.unlink()
        self._enable_inside_mode()

        line = self._create_document_line(100.0)

        self.assertEqual(line.icms_origin_percent, 7.0)
        self.assertEqual(line.icms_destination_percent, 20.5)
        self.assertEqual(line.icms_destination_base, 125.79)
        self.assertEqual(line.icms_destination_value, 16.98)
        self.assertEqual(line.icmsfcp_value, 0.0)

    def test_difal_inside_not_applied_without_difal(self):
        """Inside mode does not touch operations not subject to DIFAL."""
        self._enable_inside_mode()
        self.partner = self.env.ref("l10n_br_base.res_partner_cliente1_sp")

        line = self._create_document_line(100.0)

        self.assertEqual(line.icms_destination_base, 0.0)
        self.assertEqual(line.icms_destination_percent, 0.0)
        self.assertEqual(line.icms_destination_value, 0.0)

    def test_difal_oca_default_unchanged(self):
        """The standard OCA behavior is preserved on the default mode.

        Same assertions of the l10n_br_fiscal test_difal_calculation test:
        PE is a unique base state, so the DIFAL base is the operation base.
        """
        line = self._create_document_line(100.0)

        self.assertEqual(line.icms_destination_base, 100.0)
        self.assertEqual(line.icms_origin_percent, 7.0)
        self.assertEqual(line.icms_destination_percent, 20.5)
        self.assertEqual(line.icms_destination_value, 13.5)
        self.assertEqual(line.icmsfcp_base, 100.0)
        self.assertEqual(line.icmsfcp_value, 1.0)
