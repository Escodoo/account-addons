# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestResPartnerBank(TransactionCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        self.company1 = self.env["res.company"].create(
            {
                "name": "Test Company 1",
            }
        )
        self.company2 = self.env["res.company"].create(
            {
                "name": "Test Company 2",
            }
        )

    def test_copy_bank_accounts(self):

        company1_bank = self.env["res.partner.bank"].search(
            [
                ("company_id", "=", self.company1.id),
            ]
        )
        company2_bank = self.env["res.partner.bank"].search(
            [
                ("company_id", "=", self.company2.id),
            ]
        )

        self.assertEqual(len(company1_bank), 1)
        self.assertEqual(len(company2_bank), 1)

    def test_create_no_sync_partner_bank(self):
        bank = self.env["res.partner.bank"].create(
            {
                "acc_number": "987654321",
                "partner_id": self.partner.id,
                "company_id": self.company1.id,
            }
        )

        company2_bank = self.env["res.partner.bank"].search(
            [
                ("company_id", "=", self.company2.id),
                ("acc_number", "=", bank.acc_number),
            ]
        )

        self.assertEqual(company2_bank.acc_number, "987654321")

    def test_write_sync_partner_bank(self):
        bank = self.env["res.partner.bank"].create(
            {
                "acc_number": "433322244",
                "partner_id": self.partner.id,
                "company_id": self.company1.id,
            }
        )
        bank.write(
            {
                "acc_number": "888444333",
            }
        )

        company2_bank = self.env["res.partner.bank"].search(
            [
                ("company_id", "=", self.company2.id),
                ("acc_number", "=", bank.acc_number),
            ]
        )

        self.assertEqual(company2_bank.acc_number, "888444333")
