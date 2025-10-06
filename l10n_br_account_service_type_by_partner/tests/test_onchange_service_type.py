# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_IN


class TestServiceTypeOnchange(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env.ref("l10n_br_base.res_partner_intel")
        cls.service_type_1009 = cls.env.ref("l10n_br_fiscal.service_type_1009")

        cls.product = cls.env["product.product"].create(
            {
                "name": "Serviço Personalizado",
                "type": "service",
                "tax_icms_or_issqn": "issqn",
                "service_type_id": cls.service_type_1009.id,
            }
        )

        cls.partner_service_type = cls.env["res.partner.service.type"].create(
            {
                "partner_id": cls.partner.id,
                "product_id": cls.product.id,
                "service_type_id": cls.service_type_1009.id,
            }
        )

        cls.move = cls.env["account.move"].new(
            {
                "move_type": "in_invoice",
                "partner_id": cls.partner.id,
                "fiscal_operation_type": FISCAL_IN,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                        },
                    )
                ],
            }
        )

    def test_line_compute_product_sets_partner_service_type(self):
        line = self.move.invoice_line_ids[0]
        line.partner_id = self.partner
        line._compute_product_fiscal_fields()
        self.assertEqual(
            line.service_type_id,
            self.service_type_1009,
        )

    def test_move_onchange_partner_sets_service_type(self):
        move = self.env["account.move"].new(
            {
                "move_type": "in_invoice",
                "fiscal_operation_type": FISCAL_IN,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                        },
                    )
                ],
            }
        )
        move.partner_id = self.partner
        move._onchange_partner_id()
        self.assertEqual(
            move.invoice_line_ids[0].service_type_id,
            self.service_type_1009,
        )
