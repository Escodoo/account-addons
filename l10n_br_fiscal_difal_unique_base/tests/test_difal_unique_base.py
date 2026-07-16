# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import SavepointCase
from odoo.tests.common import Form


class TestDifalUniqueBase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_venda")
        cls.product = cls.env.ref("product.product_product_6")

        cls.partner_double_base = cls.env.ref("l10n_br_base.res_partner_cliente9_mg")
        cls.partner_unique_base = cls.env.ref("l10n_br_base.res_partner_cliente5_pe")

    def _create_document_line(self, partner, price_unit=100.0):
        doc_form = Form(
            self.env["l10n_br_fiscal.document"].with_context(
                default_fiscal_operation_type="out",
            )
        )
        doc_form.company_id = self.company
        doc_form.partner_id = partner
        doc_form.fiscal_operation_id = self.fiscal_operation

        with doc_form.fiscal_line_ids.new() as line_form:
            line_form.product_id = self.product
            line_form.price_unit = price_unit
            line_form.quantity = 1.0

        doc = doc_form.save()
        return doc.fiscal_line_ids[0]

    def test_double_base_state_final_customer_uses_unique_base(self):
        """A non taxpayer final customer in a double base state uses the base"""
        self.partner_double_base.ind_ie_dest = "9"
        self.partner_double_base.ind_final = "1"

        line = self._create_document_line(self.partner_double_base)

        self.assertTrue(line.icms_base)
        self.assertEqual(line.icms_destination_base, line.icms_base)

    def test_double_base_state_not_final_customer_keeps_double_base(self):
        """When it is not a final customer operation the core result stands"""
        self.partner_double_base.ind_ie_dest = "9"
        self.partner_double_base.ind_final = "0"

        line = self._create_document_line(self.partner_double_base)

        self.assertTrue(line.icms_destination_base)
        self.assertNotEqual(line.icms_destination_base, line.icms_base)

    def test_unique_base_state_final_customer_unchanged(self):
        """A non taxpayer final customer in a unique base state keeps OCA"""
        self.partner_unique_base.ind_ie_dest = "9"
        self.partner_unique_base.ind_final = "1"

        line = self._create_document_line(self.partner_unique_base)

        self.assertEqual(line.icms_destination_base, 100.0)
        self.assertEqual(line.icms_origin_percent, 7.0)
        self.assertEqual(line.icms_destination_percent, 20.5)
        self.assertEqual(line.icms_destination_value, 13.5)

    def test_taxpayer_partner_not_affected(self):
        """A taxpayer partner is not subject to DIFAL, nothing changes."""
        self.partner_double_base.ind_ie_dest = "1"

        line = self._create_document_line(self.partner_double_base)

        self.assertEqual(line.icms_destination_base, 0.0)
        self.assertEqual(line.icms_destination_value, 0.0)
