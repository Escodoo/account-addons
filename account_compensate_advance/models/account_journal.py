# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models

ACCOUNT_TYPES = [
    ("supplier", _("Supplier")),
    ("customer", _("Customer")),
]


class AccountJournal(models.Model):

    _inherit = "account.journal"

    is_advance_journal = fields.Boolean(
        string="Is Compensation Advance Journal",
        help="Check this box if this journal is for compensation advances",
    )
