# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from psycopg2.extensions import AsIs

from odoo import api, fields, models, tools


class AccountMoveLineCashBasisReport(models.Model):

    _name = "account.move.line.cash.basis.report"
    _description = "Account Move Line Cash Basis Report"
    _auto = False

    name = fields.Char(
        readonly=True,
    )
    ref = fields.Char(readonly=True)
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Journal Entry",
        auto_join=True,
        readonly=True,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account",
        auto_join=True,
        index=True,
        readonly=True,
    )
    account_group_id = fields.Many2one(
        comodel_name="account.group",
        string="Account Group",
        auto_join=True,
        index=True,
        readonly=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        auto_join=True,
        index=True,
        readonly=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        auto_join=True,
        readonly=True,
        index=True,
    )
    quantity = fields.Float(
        string="Quantity",
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        auto_join=True,
        readonly=True,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        auto_join=True,
        readonly=True,
        index=True,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        auto_join=True,
        readonly=True,
        index=True,
    )
    credit = fields.Float(
        readonly=True,
    )
    debit = fields.Float(
        readonly=True,
    )
    balance = fields.Float(
        readonly=True,
    )
    amount_currency = fields.Float(
        readonly=True,
    )
    amount_residual = fields.Float(
        readonly=True,
    )
    date = fields.Date(
        readonly=True,
        index=True,
    )
    reconciled = fields.Boolean(
        readonly=True,
    )
    full_reconcile_id = fields.Many2one(
        "account.full.reconcile",
        string="Matching Number",
        readonly=True,
        index=True,
    )
    statement_id = fields.Many2one(
        "account.bank.statement",
        string="Statement",
        readonly=True,
        index=True,
    )
    user_type_id = fields.Many2one(
        comodel_name="account.account.type",
        string="User Type",
        auto_join=True,
        readonly=True,
        index=True,
    )
    account_internal_type = fields.Selection(
        selection="_selection_account_internal_type", readonly=True
    )
    account_internal_group = fields.Selection(
        selection="_selection_account_internal_group", readonly=True
    )
    state = fields.Selection(
        selection="_selection_parent_state",
    )
    parent_state = fields.Selection(
        selection="_selection_parent_state",
    )
    exclude_from_invoice_tab = fields.Boolean(readonly=True)
    analytic_line_ids = fields.One2many(
        "account.analytic.line",
        "move_id",
        string="Analytic Lines",
        auto_join=True,
        readonly=True,
        index=True,
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag",
        relation="account_analytic_tag_account_move_line_rel",
        column1="account_move_line_id",
        column2="account_analytic_tag_id",
    )

    def _selection_parent_state(self):
        return self.env["account.move"].fields_get(allfields=["state"])["state"][
            "selection"
        ]

    def _selection_account_internal_type(self):
        return self.env["account.account.type"].fields_get(allfields=["type"])["type"][
            "selection"
        ]

    def _selection_account_internal_group(self):
        return self.env["account.account.type"].fields_get(
            allfields=["internal_group"]
        )["internal_group"]["selection"]

    @api.model_cr
    def init(self):
        query = """
            WITH moves AS (
             SELECT
                 "account_move_line".id as id,
                 "account_move_line".move_id as move_id,
                 "account_move_line".name as name,
                 "account_move_line".ref as ref,
                 "account_move_line".company_id as company_id,
                 "account_move_line".currency_id as currency_id,
                 "account_move_line".journal_id as journal_id,
                 "account_move_line".partner_id as partner_id,
                 "account_move_line".account_id as account_id,
                 "account_move_line".product_id as product_id,
                 "account_move_line".quantity as quantity,
                 "account_move_line".analytic_account_id as analytic_account_id,
                 "account_move_line".date as date,
                 "account_move_line".amount_currency as amount_currency,
                 "account_move_line".amount_residual as amount_residual,
                 "account_move_line".balance as balance,
                 "account_move_line".debit as debit,
                 "account_move_line".credit as credit,
                 "account_move_line".reconciled as reconciled,
                 "account_move_line".full_reconcile_id as full_reconcile_id,
                 "account_move_line".statement_id as statement_id,
                 "account".user_type_id as user_type_id,
                 "account".group_id as account_group_id,
                 "account_type".type as account_internal_type,
                 "account_type".internal_group as account_internal_group
             FROM ONLY account_move_line
             JOIN ONLY account_account account ON
                "account_move_line".account_id = account.id
             JOIN ONLY account_account_type account_type ON
                "account".user_type_id = account_type.id
             WHERE (
                 "account_move_line".journal_id IN (
                    SELECT id FROM account_journal WHERE type in ('cash', 'bank')
                 )
                 OR "account_move_line".move_id NOT IN (
                     SELECT DISTINCT aml.move_id
                     FROM ONLY account_move_line aml
                     JOIN account_account account ON aml.account_id = account.id
                     WHERE account.internal_type IN ('receivable', 'payable')
                 )
             )),
                 payment_table AS (
                 SELECT
                     aml.move_id,
                     GREATEST(aml.date, aml2.date) AS date,
                     CASE WHEN (aml.balance = 0 OR sub_aml.total_per_account = 0)
                         THEN 0
                         ELSE part.amount / ABS(sub_aml.total_per_account)
                     END as matched_percentage
                 FROM account_partial_reconcile part
                 JOIN ONLY account_move_line aml ON
                    aml.id = part.debit_move_id OR aml.id = part.credit_move_id
                 JOIN ONLY account_move_line aml2 ON
                     (aml2.id = part.credit_move_id OR aml2.id = part.debit_move_id)
                     AND aml.id != aml2.id
                 JOIN (
                     SELECT move_id, account_id, ABS(SUM(balance)) AS total_per_account
                     FROM ONLY account_move_line
                     GROUP BY move_id, account_id
                 ) sub_aml ON (
                    aml.account_id = sub_aml.account_id AND aml.move_id=sub_aml.move_id
                 )
                 JOIN account_account account ON aml.account_id = account.id
                 WHERE account.internal_type IN ('receivable', 'payable')
             )
                  SELECT * FROM moves
                  UNION ALL
                  SELECT
                 "account_move_line".id as id,
                 "account_move_line".move_id as move_id,
                 "account_move_line".name as name,
                 "account_move_line".ref as ref,
                 "account_move_line".company_id as company_id,
                 "account_move_line".currency_id as currency_id,
                 "account_move_line".journal_id as journal_id,
                 "account_move_line".partner_id as partner_id,
                 "account_move_line".account_id as account_id,
                 "account_move_line".product_id as product_id,
                 "account_move_line".quantity as quantity,
                 "account_move_line".analytic_account_id as analytic_account_id,
                 ref.date as date,
                 ref.matched_percentage * "account_move_line".amount_currency as
                    amount_currency,
                 ref.matched_percentage * "account_move_line".amount_residual as
                    amount_residual,
                 ref.matched_percentage * "account_move_line".balance as balance,
                 ref.matched_percentage * "account_move_line".debit as debit,
                 ref.matched_percentage * "account_move_line".credit as credit,
                 "account_move_line".reconciled as reconciled,
                 "account_move_line".full_reconcile_id as full_reconcile_id,
                 "account_move_line".statement_id as statement_id,
                 "account".user_type_id as user_type_id,
                 "account".group_id as account_group_id,
                 "account_type".type as account_internal_type,
                 "account_type".internal_group as account_internal_group
             FROM payment_table ref
             JOIN ONLY account_move_line ON
                "account_move_line".move_id = ref.move_id
             JOIN ONLY account_account account ON
                "account_move_line".account_id = account.id
             JOIN ONLY account_account_type account_type ON
                "account".user_type_id = account_type.id
             WHERE NOT (
                 "account_move_line".journal_id IN (
                 SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                 OR "account_move_line".move_id NOT IN (
                     SELECT DISTINCT aml.move_id
                     FROM ONLY account_move_line aml
                     JOIN account_account account ON aml.account_id = account.id
                     WHERE account.internal_type IN ('receivable', 'payable')
                 )
             )
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute(
            "CREATE OR REPLACE VIEW %s AS %s", (AsIs(self._table), AsIs(query))
        )
