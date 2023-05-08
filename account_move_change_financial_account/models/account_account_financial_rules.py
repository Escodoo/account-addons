# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAccountFinancialRules(models.Model):

    _name = "account.account.financial.rules"
    _inherit = ["mail.thread"]
    _description = "Account Account Financial Rules"

    name = fields.Char(required=True)
    domain = fields.Char(
        string="Domain Value",
        help="Optional domain filtering of the destination data, as a Python expression",
        required=True,
    )
    financial_account_id = fields.Many2one(
        "account.account",
        company_dependent=True,
        string="Account Receivable/Payable",
        domain="["
        "'|', ('account_type', '=', 'asset_receivable'),"
        "('account_type', '=', 'liability_payable'),"
        "('deprecated', '=', False),"
        "('company_id', '=', current_company_id)"
        "]",
        help="This account will be used instead of the default one as the receivable "
        "account for the current partner",
        required=True,
    )
