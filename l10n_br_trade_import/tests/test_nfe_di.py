# Copyright (C) 2023-Today - Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestNfeDI(BaseCommon):
    """Import declarations set on invoice lines feed the NF-e DI tag."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.state_sp = cls.env.ref("base.state_br_sp")
        cls.foreign_partner = cls.env["res.partner"].create(
            {"name": "Foreign Supplier", "country_id": cls.env.ref("base.us").id}
        )
        cls.acquirer = cls.env["res.partner"].create(
            {
                "name": "Acquirer",
                "is_company": True,
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.state_sp.id,
                "vat": "62.128.834/0001-34",
            }
        )
        fiscal_operation = cls.env.ref("l10n_br_fiscal.fo_compras")
        cls.document = (
            cls.env["l10n_br_fiscal.document"]
            .with_company(cls.company)
            .create(
                {
                    "company_id": cls.company.id,
                    "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                    "issuer": "company",
                    "fiscal_operation_id": fiscal_operation.id,
                    "partner_id": cls.foreign_partner.id,
                }
            )
        )
        cls.document_line = cls.env["l10n_br_fiscal.document.line"].create(
            {
                "document_id": cls.document.id,
                "name": "Imported product",
                "fiscal_operation_id": fiscal_operation.id,
                "fiscal_operation_line_id": cls.env.ref(
                    "l10n_br_fiscal.fo_compras_compras_comercializacao"
                ).id,
                "quantity": 1,
                "price_unit": 100,
            }
        )
        cls.move = (
            cls.env["account.move"]
            .with_company(cls.company)
            .create(
                {
                    "move_type": "in_invoice",
                    "partner_id": cls.foreign_partner.id,
                    "company_id": cls.company.id,
                    "invoice_line_ids": [
                        (0, 0, {"name": "Imported product", "price_unit": 100})
                    ],
                }
            )
        )
        cls.move_line = cls.move.invoice_line_ids
        cls.move_line.fiscal_document_line_id = cls.document_line

    def _create_declaration(self, **kwargs):
        vals = {
            "document_number": "24/0000001-0",
            "document_date": fields.Date.today(),
            "customs_clearance_location": "Porto de Santos",
            "customs_clearance_state_id": self.state_sp.id,
            "customs_clearance_date": fields.Date.today(),
            "transportation_type": "maritime",
            "afrmm_value": 12.5,
            "intermediary_type": "conta_propria",
            "exporting_partner_id": self.foreign_partner.id,
        }
        vals.update(kwargs)
        return self.env["l10n_br_trade_import.declaration"].create(vals)

    def _create_addition(self, declaration):
        return self.env["l10n_br_trade_import.addition"].create(
            {
                "import_declaration_id": declaration.id,
                "addition_number": "001",
                "addtion_sequence": 2,
                "manufacturer_id": self.foreign_partner.id,
                "discount_value": 1.5,
                "drawback": "DRW-1",
            }
        )

    def test_declaration_fills_nfe_di_tag(self):
        declaration = self._create_declaration()
        addition = self._create_addition(declaration)
        self.move_line.import_addition_ids = addition
        self.env.flush_all()

        di = self.document_line.nfe40_DI
        self.assertEqual(len(di), 1)
        self.assertEqual(di.nfe40_nDI, declaration.document_number)
        self.assertEqual(di.nfe40_dDI, declaration.document_date)
        self.assertEqual(di.nfe40_xLocDesemb, "Porto de Santos")
        self.assertEqual(di.nfe40_dDesemb, declaration.customs_clearance_date)
        self.assertEqual(di.nfe40_UFDesemb, "SP")
        self.assertEqual(di.nfe40_tpViaTransp, "1")
        self.assertEqual(di.nfe40_vAFRMM, 12.5)
        self.assertEqual(di.nfe40_tpIntermedio, "1")
        self.assertEqual(di.nfe40_cExportador, str(self.foreign_partner.id))

        self.assertEqual(len(di.nfe40_adi), 1)
        adi = di.nfe40_adi
        self.assertEqual(adi.nfe40_nAdicao, "001")
        self.assertEqual(adi.nfe40_nSeqAdic, "2")
        self.assertEqual(adi.nfe40_cFabricante, str(self.foreign_partner.id))
        self.assertEqual(adi.nfe40_vDescDI, 1.5)
        self.assertEqual(adi.nfe40_nDraw, "DRW-1")

    def test_declaration_with_third_party_fills_acquirer_tags(self):
        declaration = self._create_declaration(
            intermediary_type="conta_ordem",
            third_party_partner_id=self.acquirer.id,
        )
        addition = self._create_addition(declaration)
        self.move_line.import_addition_ids = addition
        self.env.flush_all()

        di = self.document_line.nfe40_DI
        self.assertEqual(len(di), 1)
        self.assertEqual(di.nfe40_tpIntermedio, "2")
        self.assertEqual(di.partner_acquirer_id, self.acquirer)
        self.assertEqual(di.nfe40_UFTerceiro, "SP")
        self.assertTrue(di.nfe40_CNPJ)
        self.assertEqual(di.nfe40_CNPJ, self.acquirer.nfe40_CNPJ)
