# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

ACCOUNT_TYPES = [
    ("supplier", _("Supplier")),
    ("customer", _("Customer")),
]
DOMAIN_ADVANCE_ACCOUNT = [
    ("user_type_id.type", "!=", "payable"),
    ("user_type_id.type", "!=", "receivable"),
    ("reconcile", "=", True),
]


class AccountJournal(models.Model):

    _inherit = "account.journal"

    is_advance_journal = fields.Boolean(
        string="Is Advance Journal",
        help="Check this box if this journal is for advances",
    )

    advance_account_type = fields.Selection(
        selection=ACCOUNT_TYPES,
        string="Advance Account Type",
        help="Select the type of advance account to be filled",
        default="supplier",
    )

    advance_account_supplier_id = fields.Many2one(
        "account.account",
        string="Advance Account for Suppliers",
        domain=DOMAIN_ADVANCE_ACCOUNT,
        help="Advance account for supplier payments",
    )

    advance_account_customer_id = fields.Many2one(
        "account.account",
        string="Advance Account for Customers",
        domain=DOMAIN_ADVANCE_ACCOUNT,
        help="Advance account for customer payments",
    )

    @api.onchange("advance_account_type", "is_advance_journal")
    def _onchange_clear_advance_account_info(self):
        self.advance_account_supplier_id = False
        self.advance_account_customer_id = False
