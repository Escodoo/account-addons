# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from odoo.addons.account.models.account_account import (
    AccountGroup as AccountGroupInherit,
)


class AccountGroup(models.Model):
    _inherit = "account.group"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "code_prefix_start" in vals and not vals.get("code_prefix_end"):
                vals["code_prefix_end"] = vals["code_prefix_start"]
        return super(AccountGroupInherit, self).create(vals_list)

    def write(self, vals):
        return super(AccountGroupInherit, self).write(vals)
