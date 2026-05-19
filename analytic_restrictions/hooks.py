# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api

_ORIGINAL_PERMS = {
    "analytic.access_account_analytic_account": (1, 1, 1, 1),
    "analytic.access_account_analytic_line": (1, 1, 1, 1),
    "analytic.access_account_analytic_distribution_model": (1, 1, 1, 1),
    "analytic.access_account_analytic_plan": (1, 1, 1, 1),
    "analytic.access_account_analytic_applicability": (1, 1, 1, 1),
    "account_analytic_tag.access_account_analytic_tag_manager": (1, 1, 1, 1),
    "project.access_account_analytic_line_project": (1, 1, 1, 1),
    "account.access_account_analytic_accountant": (1, 1, 1, 1),
    "account.access_account_analytic_plan_accountant": (1, 1, 1, 1),
    "account.access_account_analytic_applicability_accountant": (1, 1, 1, 1),
    "account.access_account_analytic_distribution_invoice": (1, 1, 1, 1),
    "hr_timesheet.access_account_analytic_user": (1, 1, 0, 0),
}


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, (
        perm_read,
        perm_write,
        perm_create,
        perm_unlink,
    ) in _ORIGINAL_PERMS.items():
        acl = env.ref(xmlid, raise_if_not_found=False)
        if not acl:
            continue
        acl.write(
            {
                "perm_read": bool(perm_read),
                "perm_write": bool(perm_write),
                "perm_create": bool(perm_create),
                "perm_unlink": bool(perm_unlink),
            }
        )
