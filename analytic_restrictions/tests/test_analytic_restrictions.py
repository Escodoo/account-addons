# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAnalyticRestrictions(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group_analytic = cls.env.ref("analytic.group_analytic_accounting")
        cls.group_admin = cls.env.ref(
            "analytic_restrictions.group_analytic_accounting_admin"
        )

        cls.model_names = [
            cls.env.ref("analytic.model_account_analytic_account").model,
            cls.env.ref("analytic.model_account_analytic_line").model,
            cls.env.ref("analytic.model_account_analytic_distribution_model").model,
            cls.env.ref("analytic.model_account_analytic_plan").model,
            cls.env.ref("analytic.model_account_analytic_applicability").model,
            cls.env.ref("account_analytic_tag.model_account_analytic_tag").model,
        ]

        cls.user_analytic = cls.env["res.users"].create(
            {
                "name": "Analytic User (RO)",
                "login": "analytic_ro",
                "email": "analytic_ro@example.com",
                "groups_id": [(6, 0, [cls.group_analytic.id])],
            }
        )
        cls.user_admin = cls.env["res.users"].create(
            {
                "name": "Analytic Admin (RW)",
                "login": "analytic_admin",
                "email": "analytic_admin@example.com",
                "groups_id": [(6, 0, [cls.group_admin.id])],
            }
        )

    def test_acl_records_loaded(self):
        ro = self.env.ref("analytic.access_account_analytic_account")
        self.assertTrue(ro.perm_read)
        self.assertFalse(ro.perm_write)
        self.assertFalse(ro.perm_create)
        self.assertFalse(ro.perm_unlink)
        self.assertEqual(ro.group_id, self.group_analytic)

        admin = self.env.ref(
            "analytic_restrictions.access_account_analytic_account_admin"
        )
        self.assertTrue(admin.perm_read)
        self.assertTrue(admin.perm_write)
        self.assertTrue(admin.perm_create)
        self.assertTrue(admin.perm_unlink)
        self.assertEqual(admin.group_id, self.group_admin)

    def test_analytic_group_is_read_only(self):
        for model_name in self.model_names:
            m = self.env[model_name].with_user(self.user_analytic)
            self.assertTrue(
                m.check_access_rights("read", raise_exception=False), model_name
            )
            self.assertFalse(
                m.check_access_rights("create", raise_exception=False), model_name
            )
            self.assertFalse(
                m.check_access_rights("write", raise_exception=False), model_name
            )
            self.assertFalse(
                m.check_access_rights("unlink", raise_exception=False), model_name
            )
