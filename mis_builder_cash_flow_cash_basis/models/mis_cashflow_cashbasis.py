# Copyright 2023 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import fields, models


class MisCashflowCashbasis(models.Model):

    _name = "mis.cashflow.cashbasis"
    # _inherit = 'account.move.line'
    _description = "Mis Cashflow Cashbasis"
    _auto = False

    # date = fields.Date(related='date_maturity')

    line_type = fields.Selection(
        [("forecast_line", "Forecast Line"), ("move_line", "Journal Item")],
        index=True,
        readonly=True,
    )
    name = fields.Char(
        readonly=True,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account",
        auto_join=True,
        index=True,
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        readonly=True,
    )
    move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Journal Item",
        auto_join=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
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
    account_internal_type = fields.Selection(
        related="account_id.user_type_id.type", readonly=True
    )
    state = fields.Selection(
        selection="_selection_parent_state",
    )

    state = fields.Selection(
        selection="_selection_parent_state",
    )

    def _selection_parent_state(self):
        return self.env["account.move"].fields_get(allfields=["state"])["state"][
            "selection"
        ]

    # def init(self):
    #     self.env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='account_move_line'")
    #     changed_fields = ['date', 'amount_currency', 'amount_residual', 'balance', 'debit', 'credit']
    #     unchanged_fields = list(set(f[0] for f in self.env.cr.fetchall()) - set(changed_fields))
    #
    #     query = """
    #         WITH moves AS (
    #         SELECT
    #             'move_line' as line_type,
    #             {unchanged_fields},
    #             "account_move_line".date as date,
    #             "account_move_line".amount_currency as amount_currency,
    #             "account_move_line".amount_residual as amount_residual,
    #             "account_move_line".balance as balance,
    #             "account_move_line".debit as debit,
    #             "account_move_line".credit as credit
    #         FROM ONLY account_move_line
    #         WHERE (
    #             "account_move_line".journal_id IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
    #             OR "account_move_line".move_id NOT IN (
    #                 SELECT DISTINCT aml.move_id
    #                 FROM ONLY account_move_line aml
    #                 JOIN account_account account ON aml.account_id = account.id
    #                 WHERE account.internal_type IN ('receivable', 'payable')
    #             )
    #         )),
    #             payment_table AS (
    #             SELECT
    #                 aml.move_id,
    #                 GREATEST(aml.date, aml2.date) AS date,
    #                 CASE WHEN (aml.balance = 0 OR sub_aml.total_per_account = 0)
    #                     THEN 0
    #                     ELSE part.amount / ABS(sub_aml.total_per_account)
    #                 END as matched_percentage
    #             FROM account_partial_reconcile part
    #             JOIN ONLY account_move_line aml ON aml.id = part.debit_move_id OR aml.id = part.credit_move_id
    #             JOIN ONLY account_move_line aml2 ON
    #                 (aml2.id = part.credit_move_id OR aml2.id = part.debit_move_id)
    #                 AND aml.id != aml2.id
    #             JOIN (
    #                 SELECT move_id, account_id, ABS(SUM(balance)) AS total_per_account
    #                 FROM ONLY account_move_line
    #                 GROUP BY move_id, account_id
    #             ) sub_aml ON (aml.account_id = sub_aml.account_id AND aml.move_id=sub_aml.move_id)
    #             JOIN account_account account ON aml.account_id = account.id
    #             WHERE account.internal_type IN ('receivable', 'payable')
    #         )
    #              SELECT * FROM moves
    #              UNION ALL
    #              SELECT
    #             'move_line' as line_type,
    #             {unchanged_fields},
    #             ref.date as date,
    #             ref.matched_percentage * "account_move_line".amount_currency as amount_currency,
    #             ref.matched_percentage * "account_move_line".amount_residual as amount_residual,
    #             ref.matched_percentage * "account_move_line".balance as balance,
    #             ref.matched_percentage * "account_move_line".debit as debit,
    #             ref.matched_percentage * "account_move_line".credit as credit
    #         FROM payment_table ref
    #         JOIN ONLY account_move_line ON "account_move_line".move_id = ref.move_id
    #         WHERE NOT (
    #             "account_move_line".journal_id IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
    #             OR "account_move_line".move_id NOT IN (
    #                 SELECT DISTINCT aml.move_id
    #                 FROM ONLY account_move_line aml
    #                 JOIN account_account account ON aml.account_id = account.id
    #                 WHERE account.internal_type IN ('receivable', 'payable')
    #             )
    #         )
    #     """.format(
    #             all_fields=', '.join(f'"{f}"' for f in (unchanged_fields + changed_fields)),
    #             unchanged_fields=', '.join([f'"account_move_line"."{f}"' for f in unchanged_fields])
    #     )
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #     self._cr.execute(
    #         "CREATE OR REPLACE VIEW %s AS (%s)", (AsIs(self._table), AsIs(query))
    #     )

    @property
    def _table_query(self):
        # self.env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name='account_move_line'")
        # changed_fields = ['date', 'amount_currency', 'amount_residual', 'balance', 'debit', 'credit']
        # unchanged_fields = list(set(f[0] for f in self.env.cr.fetchall()) - set(changed_fields))

        return """
             WITH moves AS (
             SELECT
                 "account_move_line".id as id,
                 "account_move_line".name as name,
                 "account_move_line".parent_state as state,
                 'move_line' as line_type,
                 "account_move_line".company_id as company_id,
                 "account_move_line".journal_id as journal_id,
                 "account_move_line".partner_id as partner_id,
                 "account_move_line".account_id as account_id,
                 "account_move_line".date as date,
                 "account_move_line".amount_currency as amount_currency,
                 "account_move_line".amount_residual as amount_residual,
                 "account_move_line".balance as balance,
                 "account_move_line".debit as debit,
                 "account_move_line".credit as credit,
                 "account_move_line".reconciled as reconciled,
                 "account_move_line".full_reconcile_id as full_reconcile_id
             FROM ONLY account_move_line
             WHERE (
                 "account_move_line".journal_id IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
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
                 JOIN ONLY account_move_line aml ON aml.id = part.debit_move_id OR aml.id = part.credit_move_id
                 JOIN ONLY account_move_line aml2 ON
                     (aml2.id = part.credit_move_id OR aml2.id = part.debit_move_id)
                     AND aml.id != aml2.id
                 JOIN (
                     SELECT move_id, account_id, ABS(SUM(balance)) AS total_per_account
                     FROM ONLY account_move_line
                     GROUP BY move_id, account_id
                 ) sub_aml ON (aml.account_id = sub_aml.account_id AND aml.move_id=sub_aml.move_id)
                 JOIN account_account account ON aml.account_id = account.id
                 WHERE account.internal_type IN ('receivable', 'payable')
             )
                  SELECT * FROM moves
                  UNION ALL
                  SELECT
                 "account_move_line".id as id,
                 "account_move_line".name as name,
                 "account_move_line".parent_state as state,
                 'move_line' as line_type,
                 "account_move_line".company_id as company_id,
                 "account_move_line".journal_id as journal_id,
                 "account_move_line".partner_id as partner_id,
                 "account_move_line".account_id as account_id,
                 ref.date as date,
                 ref.matched_percentage * "account_move_line".amount_currency as amount_currency,
                 ref.matched_percentage * "account_move_line".amount_residual as amount_residual,
                 ref.matched_percentage * "account_move_line".balance as balance,
                 ref.matched_percentage * "account_move_line".debit as debit,
                 ref.matched_percentage * "account_move_line".credit as credit,
                 "account_move_line".reconciled as reconciled,
                 "account_move_line".full_reconcile_id as full_reconcile_id
             FROM payment_table ref
             JOIN ONLY account_move_line ON "account_move_line".move_id = ref.move_id
             WHERE NOT (
                 "account_move_line".journal_id IN (SELECT id FROM account_journal WHERE type in ('cash', 'bank'))
                 OR "account_move_line".move_id NOT IN (
                     SELECT DISTINCT aml.move_id
                     FROM ONLY account_move_line aml
                     JOIN account_account account ON aml.account_id = account.id
                     WHERE account.internal_type IN ('receivable', 'payable')
                 )
             )
         """
