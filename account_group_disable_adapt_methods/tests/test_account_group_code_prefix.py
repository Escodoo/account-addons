# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestAccountGroupCodePrefix(TransactionCase):
    def test_create_with_only_code_prefix_start(self):
        group = self.env["account.group"].create(
            {
                "name": "Grupo Receita",
                "code_prefix_start": "1",
            }
        )
        self.assertEqual(group.code_prefix_start, "1")
        self.assertEqual(group.code_prefix_end, "1")

    def test_create_with_both_code_prefixes(self):
        group = self.env["account.group"].create(
            {
                "name": "Grupo Despesa",
                "code_prefix_start": "2",
                "code_prefix_end": "5",
            }
        )
        self.assertEqual(group.code_prefix_start, "2")
        self.assertEqual(group.code_prefix_end, "5")

    def test_create_without_prefixes(self):
        group = self.env["account.group"].create(
            {
                "name": "Grupo Sem Prefixo",
            }
        )
        self.assertFalse(group.code_prefix_start)
        self.assertFalse(group.code_prefix_end)
