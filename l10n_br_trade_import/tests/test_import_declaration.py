# Copyright (C) 2023-Today - Engenere (<https://engenere.one>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestImportDeclaration(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.declaration_model = cls.env["l10n_br_trade_import.declaration"]
        cls.addition_model = cls.env["l10n_br_trade_import.addition"]
        cls.state_sp = cls.env.ref("base.state_br_sp")
        cls.manufacturer = cls.env["res.partner"].create({"name": "Foreign Maker"})
        cls.acquirer = cls.env["res.partner"].create({"name": "Acquirer"})

    def _declaration_vals(self, **kwargs):
        vals = {
            "document_number": "24/0000001-0",
            "document_date": fields.Date.today(),
            "customs_clearance_location": "Porto de Santos",
            "customs_clearance_state_id": self.state_sp.id,
            "customs_clearance_date": fields.Date.today(),
            "transportation_type": "aerial",
            "intermediary_type": "conta_propria",
        }
        vals.update(kwargs)
        return vals

    def test_create_declaration_with_additions(self):
        declaration = self.declaration_model.create(self._declaration_vals())
        addition = self.addition_model.create(
            {
                "import_declaration_id": declaration.id,
                "addition_number": "001",
                "addtion_sequence": 1,
                "manufacturer_id": self.manufacturer.id,
            }
        )
        self.assertEqual(declaration.addition_ids, addition)
        self.assertEqual(addition.import_declaration_number, declaration.document_number)
        self.assertEqual(addition.import_declaration_date, declaration.document_date)

    def test_third_party_required_when_not_own_account(self):
        for intermediary_type in ("conta_ordem", "encomenda"):
            with self.assertRaises(UserError):
                self.declaration_model.create(
                    self._declaration_vals(intermediary_type=intermediary_type)
                )
            declaration = self.declaration_model.create(
                self._declaration_vals(
                    intermediary_type=intermediary_type,
                    third_party_partner_id=self.acquirer.id,
                )
            )
            self.assertEqual(declaration.third_party_partner_id, self.acquirer)

    def test_afrmm_required_for_maritime_transport(self):
        with self.assertRaises(UserError):
            self.declaration_model.create(
                self._declaration_vals(transportation_type="maritime")
            )
        declaration = self.declaration_model.create(
            self._declaration_vals(transportation_type="maritime", afrmm_value=10.0)
        )
        self.assertEqual(declaration.afrmm_value, 10.0)
