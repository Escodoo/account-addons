# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import sql

from odoo import api, models


class AccountReconciliation(models.AbstractModel):

    _inherit = "account.reconciliation.widget"

    @api.model
    def get_move_lines_for_bank_statement_line(
        self,
        st_line_id,
        partner_id=None,
        excluded_ids=None,
        search_str=False,
        offset=0,
        limit=None,
        mode=None,
    ):
        """
        Rewrite of the function to return move lines for the
        Bank statement reconciliation widget.
        Modifies the order of fields 'date_maturity' and 'id' to DESC,
        moving 'date_maturity' to the first position and '{amout}' to the second.
        """
        st_line = self.env["account.bank.statement.line"].browse(st_line_id)

        # Blue lines = payment on bank account not assigned to a statement yet
        aml_accounts = [
            st_line.journal_id.default_account_id.id,
        ]

        if partner_id is None:
            partner_id = st_line.partner_id.id

        domain = self._domain_move_lines_for_reconciliation(
            st_line,
            aml_accounts,
            partner_id,
            excluded_ids=excluded_ids,
            search_str=search_str,
            mode=mode,
        )

        from_clause, where_clause, where_clause_params = (
            self.env["account.move.line"]._where_calc(domain).get_sql()
        )

        query_str = sql.SQL(
            """
            SELECT "account_move_line".id, COUNT(*) OVER() FROM {from_clause}
            {where_str}
            ORDER BY "account_move_line".date_maturity DESC,
                ("account_move_line".debit -
                "account_move_line".credit) = {amount} DESC,
                "account_move_line".id DESC
            {limit_str}
        """.format(
                from_clause=from_clause,
                where_str=where_clause and (" WHERE %s" % where_clause) or "",
                amount=st_line.amount,
                limit_str=limit and " LIMIT %s" or "",
            )
        )
        params = where_clause_params + (limit and [limit] or [])
        self.env["account.move"].flush()
        self.env["account.move.line"].flush()
        self.env["account.bank.statement"].flush()
        self._cr.execute(query_str, params)
        res = self._cr.fetchall()
        try:
            # All records will have the same count value, just get the 1st one
            recs_count = res[0][1]
        except IndexError:
            recs_count = 0
        aml_recs = self.env["account.move.line"].browse([i[0] for i in res])
        target_currency = (
            st_line.foreign_currency_id
            or st_line.journal_id.currency_id
            or st_line.journal_id.company_id.currency_id
        )
        return self._prepare_move_lines(
            aml_recs,
            target_currency=target_currency,
            target_date=st_line.date,
            recs_count=recs_count,
        )
