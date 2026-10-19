# Copyright 2026 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import uuid
from datetime import date
from types import SimpleNamespace

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountStatementImport(TransactionCase):
    def test_prepare_ofx_transaction_line_sets_unique_import_id(self):
        import_wizard = self.env["account.statement.import"]
        transaction = SimpleNamespace(
            payee="Supplier ABC",
            checknum="123",
            memo="Pagamento",
            date=date(2026, 1, 1),
            amount=100.0,
            id="OFX_TX_001",
        )

        vals_first = import_wizard._prepare_ofx_transaction_line(transaction)
        vals_second = import_wizard._prepare_ofx_transaction_line(transaction)

        self.assertIn("unique_import_id", vals_first)
        self.assertIsInstance(vals_first["unique_import_id"], str)
        self.assertTrue(vals_first["unique_import_id"])
        self.assertEqual(vals_first["payment_ref"], "Supplier ABC 123 : Pagamento")
        self.assertEqual(vals_first["amount"], 100.0)
        self.assertEqual(vals_first["date"], date(2026, 1, 1))

        uuid.UUID(vals_first["unique_import_id"])
        uuid.UUID(vals_second["unique_import_id"])
        self.assertNotEqual(vals_first["unique_import_id"], transaction.id)
        self.assertNotEqual(
            vals_first["unique_import_id"], vals_second["unique_import_id"]
        )
