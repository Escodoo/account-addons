# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo.modules.module import get_module_resource
from odoo.tests.common import TransactionCase

ACCOUNT_NUMBER = "1234567890"
OFX_FILENAME = "test_ofx_itau_accents.ofx"


class TestOfxUnaccent(TransactionCase):
    """Tests for OFX files whose header declares CHARSET:1252 while the
    content is actually written in UTF-8, as the ones exported by Itau."""

    def setUp(self):
        super().setUp()
        self.asi_model = self.env["account.statement.import"]
        self.abs_model = self.env["account.bank.statement"]
        self.absl_model = self.env["account.bank.statement.line"]

        company = self.env.ref("base.main_company")
        currency = self.env.ref("base.BRL")
        currency.active = True
        bank_account = self.env["res.partner.bank"].create(
            {
                "acc_number": ACCOUNT_NUMBER,
                "partner_id": self.env.ref("base.main_partner").id,
                "company_id": company.id,
                "bank_id": self.env.ref("base.res_bank_1").id,
            }
        )
        suspense_account = self.env["account.account"].create(
            {
                "name": "Bank Suspense Account TEST OFX UNACCENT",
                "code": "SUSPOFX",
                "user_type_id": self.env.ref(
                    "account.data_account_type_current_liabilities"
                ).id,
                "company_id": company.id,
                "reconcile": False,
            }
        )
        self.env["account.journal"].create(
            {
                "name": "Bank Journal TEST OFX UNACCENT",
                "code": "BNK14",
                "type": "bank",
                "bank_account_id": bank_account.id,
                "currency_id": currency.id,
                "suspense_account_id": suspense_account.id,
            }
        )
        self.ofx_data = open(
            get_module_resource(
                "account_statement_import_ofx_unaccent",
                "tests/test_ofx_file/",
                OFX_FILENAME,
            ),
            "rb",
        ).read()

    def test_sanitize_ofx_accents(self):
        """Accented characters are replaced by their ASCII equivalent."""
        self.assertIn("SAÍDA".encode(), self.ofx_data)
        sanitized = self.asi_model._sanitize_ofx_accents(self.ofx_data)
        self.assertIn(b"SAIDA", sanitized)
        self.assertNotIn("SAÍDA".encode(), sanitized)
        # The whole file is now plain ASCII, so decoding it as the CHARSET
        # declared in the OFX header no longer raises.
        self.assertEqual(sanitized.decode("cp1252"), sanitized.decode("ascii"))

    def test_check_ofx_with_accents(self):
        """The accented file is recognized as a valid OFX file."""
        self.assertTrue(self.asi_model._check_ofx(self.ofx_data))

    def test_ofx_file_import(self):
        """The accented file is imported without the 'invalid file' error."""
        wizard = self.asi_model.create(
            {
                "statement_file": base64.b64encode(self.ofx_data),
                "statement_filename": OFX_FILENAME,
            }
        )
        wizard.import_file_button()

        statement = self.abs_model.search([("name", "like", ACCOUNT_NUMBER)])[0]
        self.assertAlmostEqual(statement.balance_start, 0.0)
        self.assertAlmostEqual(statement.balance_end_real, -100.0)
        self.assertEqual(len(statement.line_ids), 1)

        payment_ref = statement.line_ids.payment_ref
        self.assertIn("SAIDA PIX ENVIADO", payment_ref)
        self.assertNotIn("Í", payment_ref)
