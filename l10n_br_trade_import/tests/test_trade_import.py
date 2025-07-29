from datetime import date

from odoo.tests.common import TransactionCase


class TestImportDeclaration(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_exporter = cls.env["res.partner"].create({"name": "Exportador"})
        cls.partner_buyer = cls.env.ref("l10n_br_base.res_partner_cliente1_sp")

        cls.refund_journal = cls.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", cls.env.company.id)], limit=1
        )

        cls.invoice = cls.env["account.move"].create(
            {
                "name": "Test Invoice",
                "move_type": "out_invoice",
                "partner_id": cls.partner_buyer.id,
                "invoice_payment_term_id": cls.env.ref(
                    "account.account_payment_term_advance"
                ).id,
                "journal_id": cls.refund_journal.id,
                "document_type_id": cls.env.ref("l10n_br_fiscal.document_55").id,
                "document_serie_id": cls.env.ref(
                    "l10n_br_fiscal.empresa_lc_document_55_serie_1"
                ).id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_product_6").id,
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "account_id": cls.env["account.account"]
                            .search(
                                [
                                    ("account_type", "=", "income"),
                                    ("company_id", "=", cls.env.company.id),
                                ],
                                limit=1,
                            )
                            .id,
                            "name": "Produto importado",
                            "uom_id": cls.env.ref("uom.product_uom_unit").id,
                        },
                    )
                ],
            }
        )

        cls.import_declaration = cls.env["l10n_br_trade_import.declaration"].create(
            {
                "document_number": "123",
                "document_date": date(2024, 1, 10),
                "customs_clearance_location": "Porto de Santos",
                "customs_clearance_state_id": cls.env.ref("base.state_br_sp").id,
                "customs_clearance_date": date(2024, 1, 15),
                "transportation_type": "maritime",
                "afrmm_value": 1000.00,
                "intermediary_type": "conta_propria",
                "exporting_partner_id": cls.partner_exporter.id,
            }
        )

        cls.addition = cls.env["l10n_br_trade_import.addition"].create(
            {
                "import_declaration_id": cls.import_declaration.id,
                "addition_number": 1,
                "addtion_sequence": 1,
                "manufacturer_id": cls.partner_exporter.id,
                "discount_value": 100,
                "drawback": "DBK123",
            }
        )
        cls.invoice.line_ids[0].import_addition_ids = [(6, 0, [cls.addition.id])]
        cls.invoice.action_post()
        cls.invoice.fiscal_document_id.action_document_confirm()

    def test_compute_nfe40_DI(self):
        self.invoice.line_ids._compute_nfe40_DI()
        self.assertEqual(self.invoice.line_ids[0].nfe40_xLocDesemb, "Porto de Santos")
