# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# Copyright 2025 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestResPartnerBank(TransactionCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        cls.company1 = cls.env["res.company"].create(
            {
                "name": "Test Company 1",
            }
        )
        cls.company2 = cls.env["res.company"].create(
            {
                "name": "Test Company 2",
            }
        )

    def test_copy_bank_accounts(self):
        self.env["res.partner.bank"].create(
            {
                "acc_number": "123456789",
                "partner_id": self.company1.partner_id.id,
                "company_id": self.company1.id,
            }
        )

        company1_bank = self.env["res.partner.bank"].search(
            [
                ("partner_id", "=", self.company1.partner_id.id),
                ("acc_number", "=", "123456789"),
            ]
        )
        company2_bank = self.env["res.partner.bank"].search(
            [
                ("partner_id", "=", self.company2.partner_id.id),
                ("acc_number", "=", "123456789"),
            ]
        )

        self.assertEqual(len(company1_bank), 1)
        self.assertEqual(len(company2_bank), 1)

    def test_create_no_sync_partner_bank(self):
        bank = self.env["res.partner.bank"].create(
            {
                "acc_number": "987654321",
                "partner_id": self.company1.partner_id.id,
                "company_id": self.company1.id,
            }
        )

        company2_bank = self.env["res.partner.bank"].search(
            [
                ("partner_id", "=", self.company2.partner_id.id),
                ("acc_number", "=", bank.acc_number),
            ],
            limit=1,
        )

        self.assertEqual(company2_bank.acc_number, "987654321")

    def test_write_sync_partner_bank(self):
        bank = self.env["res.partner.bank"].create(
            {
                "acc_number": "433322244",
                "partner_id": self.company1.partner_id.id,
                "company_id": self.company1.id,
            }
        )
        bank.write({"acc_number": "888444333"})

        company2_bank = self.env["res.partner.bank"].search(
            [
                ("partner_id", "=", self.company2.partner_id.id),
                ("acc_number", "=", "888444333"),
            ],
            limit=1,
        )

        self.assertEqual(company2_bank.acc_number, "888444333")
