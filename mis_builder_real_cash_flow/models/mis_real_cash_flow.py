# Copyright 2025 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2.extensions import AsIs

from odoo import fields, models, tools


class MisRealCashFlow(models.Model):

    _name = "mis.real.cash_flow"
    _description = "MIS Real Cash Flow"
    _auto = False

    date = fields.Date(
        readonly=True,
        index=True,
    )
    line_type = fields.Selection(
        [("BANK_LINE", "Bank Line"), ("CASH_FLOW_LINE", "Cash Flow Line")],
        index=True,
        readonly=True,
    )
    move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Journal Item",
        auto_join=True,
        readonly=True,
    )
    bank_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Bank Account",
        auto_join=True,
        index=True,
        readonly=True,
    )
    state = fields.Selection(
        selection="_selection_parent_state",
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
    bank_flow = fields.Selection(
        [("ENTRADA", "Entrada"), ("SAÍDA", "Saída")],
        index=True,
        readonly=True,
    )
    account_code = fields.Char(
        readonly=True,
    )
    name = fields.Char(
        readonly=True,
    )
    full_reconcile_id = fields.Many2one(
        comodel_name="account.full.reconcile",
        string="Matching Number",
        readonly=True,
        index=True,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
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
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        readonly=True,
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        auto_join=True,
        readonly=True,
    )
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Journal Entry",
        auto_join=True,
        readonly=True,
    )
    doc_date = fields.Date(
        readonly=True,
    )
    account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account",
        auto_join=True,
        index=True,
        readonly=True,
    )
    issuer = fields.Char(
        readonly=True,
    )
    document_serie = fields.Char(
        readonly=True,
    )
    document_number = fields.Char(
        readonly=True,
    )
    amount_price_gross = fields.Float(
        readonly=True,
    )
    cnpj_cpf = fields.Char(
        readonly=True,
    )
    label = fields.Char(
        readonly=True,
    )

    def _selection_parent_state(self):
        return self.env["account.move"].fields_get(allfields=["state"])["state"][
            "selection"
        ]

    def init(self):
        query = """
            WITH rep_cf_inicial AS (
                SELECT aml.id AS x_aml_id,
                    aml.date AS x_date,
                    aml.move_id AS x_move_id,
                    aml.account_id AS x_account_account_id,
                    aml.credit AS x_credit,
                    aml.debit AS x_debit,
                    aml.balance * -1 AS x_balance,
                    CASE
                        WHEN aml.balance > 0 THEN 'SAÍDA'
                        ELSE 'ENTRADA'
                    END AS x_bank_flow,
                    aa.code AS x_account_account_code,
                    aml.name AS x_name,
                    aml.full_reconcile_id AS x_full_reconcile_id,
                    aml.journal_id AS x_journal_id,
                    aml.company_id AS x_company_id,
                    am.state AS x_state,
                    aml.statement_line_id AS x_statement_line_id,
                    aml.statement_id AS x_statement_id
                FROM account_move_line AS aml
                    INNER JOIN account_journal AS aj ON aj.id = aml.journal_id
                    INNER JOIN account_move AS am ON am.id = aml.move_id
                    INNER JOIN account_account AS aa ON aml.account_id = aa.id
                    INNER JOIN account_account_type AS aat ON aa.user_type_id = aat.id
                    INNER JOIN res_company rcp ON aml.company_id = rcp.id
                WHERE aj.type = 'bank'
                    AND aa.id != aj.default_account_id
                    AND EXISTS (
                        SELECT 1
                        FROM account_move_line AS sub_aml
                            INNER JOIN account_account AS sub_aa
                            ON sub_aml.account_id = sub_aa.id
                            INNER JOIN account_account_type AS sub_aat
                            ON sub_aa.user_type_id = sub_aat.id
                        WHERE sub_aml.move_id = aml.move_id
                            AND sub_aat.type = 'liquidity'
                    )
            ),
            rep_cf_bank_lines AS (
                SELECT aml.id AS x_aml_id,
                    aml.date AS x_date,
                    aml.move_id AS x_move_id,
                    aml.account_id AS x_account_account_id,
                    aml.credit AS x_credit,
                    aml.debit AS x_debit,
                    aml.balance AS x_balance,
                    CASE
                        WHEN aml.balance > 0 THEN 'SAÍDA'
                        ELSE 'ENTRADA'
                    END AS x_bank_flow,
                    aa.code AS x_account_account_code,
                    aml.name AS x_name,
                    aml.full_reconcile_id AS x_full_reconcile_id,
                    aml.journal_id AS x_journal_id,
                    aml.company_id AS x_company_id,
                    am.state AS x_state,
                    aml.statement_line_id AS x_statement_line_id,
                    aml.statement_id AS x_statement_id
                FROM account_move_line AS aml
                    INNER JOIN account_journal AS aj ON aj.id = aml.journal_id
                    INNER JOIN account_move AS am ON am.id = aml.move_id
                    INNER JOIN account_account AS aa ON aml.account_id = aa.id
                    INNER JOIN account_account_type AS aat ON aa.user_type_id = aat.id
                    INNER JOIN res_company rcp ON aml.company_id = rcp.id
                WHERE aj.type = 'bank'
                    AND aa.id = aj.default_account_id
                    AND EXISTS (
                        SELECT 1
                        FROM account_move_line AS sub_aml
                            INNER JOIN account_account AS sub_aa
                            ON sub_aml.account_id = sub_aa.id
                            INNER JOIN account_account_type AS sub_aat
                            ON sub_aa.user_type_id = sub_aat.id
                        WHERE sub_aml.move_id = aml.move_id
                            AND sub_aat.type = 'liquidity'
                    )
            ),
            rep_cf_outstanding_entries_counterpart AS (
                SELECT oml.id AS x_aml_id,
                    oml.move_id AS x_move_id,
                    related_aml.x_full_reconcile_id AS x_related_full_reconcile_id
                FROM account_move_line AS oml
                    INNER JOIN rep_cf_inicial AS related_aml
                    ON related_aml.x_full_reconcile_id = oml.full_reconcile_id
                    AND oml.id != related_aml.x_aml_id
                WHERE oml.account_id IN (
                        SELECT aj.payment_debit_account_id
                        FROM account_journal aj
                        WHERE aj.type = 'bank'
                        UNION
                        SELECT aj.payment_credit_account_id
                        FROM account_journal aj
                        WHERE aj.type = 'bank'
                    )
            ),
            rep_cf_account_move_line_counterpart AS (
                SELECT MAX(cml.x_aml_id) AS x_cml_id,
                    cml.x_related_full_reconcile_id AS x_related_full_reconcile_id,
                    MAX(ccml.account_id) AS x_account_id,
                    MAX(ccml.full_reconcile_id) AS x_full_reconcile_id
                FROM rep_cf_outstanding_entries_counterpart AS cml
                    INNER JOIN account_move_line AS ccml ON cml.x_move_id = ccml.move_id
                    AND ccml.id != cml.x_aml_id
                GROUP BY x_related_full_reconcile_id
            ),
            rep_cf_inicial_bank AS (
                SELECT rib.x_aml_id,
                    rib.x_date,
                    rib.x_move_id,
                    COALESCE(
                        amlc.x_account_id,
                        rib.x_account_account_id
                    ) AS x_account_account_id,
                    rib.x_credit,
                    rib.x_debit,
                    rib.x_balance,
                    rib.x_bank_flow,
                    rib.x_account_account_code,
                    rib.x_name,
                    COALESCE(
                        amlc.x_full_reconcile_id,
                        rib.x_full_reconcile_id
                    ) AS x_full_reconcile_id,
                    rib.x_journal_id,
                    rib.x_company_id,
                    rib.x_state,
                    rib.x_statement_line_id,
                    rib.x_statement_id
                FROM rep_cf_inicial rib
                    LEFT JOIN rep_cf_account_move_line_counterpart amlc
                    ON rib.x_full_reconcile_id = amlc.x_related_full_reconcile_id
            ),
            rep_cf_s_reconcil_bank AS (
                SELECT aml.id as x_aml_id,
                    MAX(aml.move_id) as x_move_id,
                    MAX(
                        CASE
                            WHEN aa.id = rcp.transfer_account_id THEN 'TRANSFER'
                            ELSE 'BANCO'
                        END
                    ) AS x_label,
                    MAX(aml.partner_id) as x_partner_id,
                    MAX(aa.id) as x_account_account_id,
                    MAX(ABS(aml.balance * -1)) as x_balance,
                    MAX(aa.code) as x_account_account_code,
                    MAX(aml.name) as x_name,
                    aml.full_reconcile_id as x_full_reconcile_id,
                    aml.date as x_date
                FROM account_move_line as aml
                    INNER JOIN account_journal as aj ON aj.id = aml.journal_id
                    INNER JOIN account_account aa ON aml.account_id = aa.id
                    INNER JOIN account_account_type aat ON aa.user_type_id = aat.id
                    INNER JOIN res_company rcp ON aml.company_id = rcp.id
                WHERE aj.type = 'bank'
                    AND aat.type != 'liquidity'
                    AND aml.full_reconcile_id is null
                    OR aa.id = rcp.transfer_account_id
                GROUP BY aml.id,
                    aml.full_reconcile_id
            ),
            ranked_moves AS (
                SELECT aml.move_id,
                    aml.account_id,
                    aml.analytic_account_id,
                    coalesce(aml.partner_id, am.partner_id) as partner_id,
                    aml.balance * -1 AS abs_balance,
                    ROW_NUMBER() OVER (
                        PARTITION BY aml.move_id
                        ORDER BY ABS(aml.balance) DESC
                    ) AS row_num
                FROM account_move_line AS aml
                    INNER JOIN account_journal AS aj ON aj.id = aml.journal_id
                    INNER JOIN account_account AS aa ON aml.account_id = aa.id
                    INNER JOIN account_move AS am ON aml.move_id = am.id
                    INNER JOIN account_account_type AS aat ON aa.user_type_id = aat.id
                    LEFT JOIN account_move_line AS rec_line
                    ON aml.full_reconcile_id = rec_line.full_reconcile_id
                WHERE aj.type IN ('purchase', 'sale')
                    AND aat.type NOT IN ('payable', 'receivable')
            ),
            rep_cf_sale_purchase_analytic_account AS (
                SELECT rm.move_id AS x_move_id,
                    rm.account_id AS x_account_account_id,
                    rm.analytic_account_id AS x_analytic_account_id,
                    rm.partner_id AS x_partner_id,
                    aa.code AS x_account_account_code,
                    MAX(rm.abs_balance) AS x_max_abs_balance
                FROM ranked_moves AS rm
                    INNER JOIN account_account AS aa ON rm.account_id = aa.id
                WHERE rm.row_num = 1
                GROUP BY rm.move_id,
                    rm.account_id,
                    aa.code,
                    rm.analytic_account_id,
                    rm.partner_id
            ),
            rep_cf_sale_purchase_journal AS (
                SELECT DISTINCT MAX(aml.date) as x_date,
                    MAX(aml.id) as x_aml_id,
                    MAX(ABS(aml.balance * -1)) as x_balance,
                    aml.full_reconcile_id as x_full_reconcile_id,
                    MAX(aml.journal_id) as x_journal_id,
                    MAX(aml.move_id) as x_move_id,
                    MAX(
                        CASE
                            WHEN aj.type = 'sale' THEN 'VENDAS'
                            ELSE 'COMPRAS'
                        END
                    ) AS x_label,
                    MAX(aml.company_id) as x_company_id,
                    MAX(COALESCE(t_aac.x_partner_id, t_rp.id, t_rpm.id)) as x_partner_id,
                    MAX(t_aac.x_analytic_account_id) as x_analytic_account_id,
                    MAX(t_aac.x_account_account_id) as x_account_account_id,
                    MAX(t_fd.issuer) as x_issuer,
                    MAX(t_fd.document_serie) as x_document_serie,
                    MAX(t_fd.document_number) as x_document_number,
                    MAX(t_fd.amount_price_gross) as x_amount_price_gross,
                    MAX(coalesce(t_rp.cnpj_cpf, t_rpm.cnpj_cpf)) as x_cnpj_cpf
                FROM account_move_line as aml
                    INNER JOIN account_journal as aj ON aj.id = aml.journal_id
                    INNER JOIN account_account aa ON aml.account_id = aa.id
                    INNER JOIN account_account_type aat ON aa.user_type_id = aat.id
                    JOIN account_move as t_am on t_am.id = aml.move_id
                    LEFT JOIN rep_cf_sale_purchase_analytic_account as t_aac
                    on t_aac.x_move_id = aml.move_id
                    LEFT JOIN res_partner as t_rpm
                    on t_rpm.id = t_am.partner_id
                    LEFT JOIN res_partner as t_rp
                    on t_rp.id = aml.partner_id
                    LEFT JOIN l10n_br_fiscal_document as t_fd
                    on t_fd.id = t_am.fiscal_document_id
                WHERE aj.type in ('sale', 'purchase')
                    AND aml.full_reconcile_id is not null
                GROUP BY aml.full_reconcile_id
            )

            SELECT DISTINCT
                aml.x_aml_id as id,
                aml.x_date as "date",
                'CASH_FLOW_LINE' as line_type,
                aml.x_aml_id as move_line_id,
                CASE
                    WHEN aml.x_account_account_id = coalesce(
                        psm.x_account_account_id,
                        brm.x_account_account_id
                    ) THEN aj.default_account_id
                    ELSE coalesce(
                        psm.x_account_account_id,
                        brm.x_account_account_id
                    )
                END as bank_account_id,
                aml.x_state as "state",
                aml.x_credit as credit,
                aml.x_debit as debit,
                aml.x_balance as balance,
                aml.x_bank_flow as bank_flow,
                aml.x_account_account_code as account_code,
                aml.x_name as "name",
                aml.x_full_reconcile_id as full_reconcile_id,
                aml.x_journal_id as journal_id,
                aml.x_company_id as company_id,
                coalesce(psm.x_partner_id, brm.x_partner_id) as partner_id,
                coalesce(psm.x_analytic_account_id, 0) as analytic_account_id,
                coalesce(psm.x_move_id, brm.x_move_id) as move_id,
                coalesce(psm.x_date, brm.x_date) as doc_date,
                coalesce(
                    psm.x_account_account_id,
                    brm.x_account_account_id
                ) as account_id,
                psm.x_issuer as issuer,
                psm.x_document_serie as document_serie,
                psm.x_document_number as document_number,
                coalesce(psm.x_amount_price_gross, 0) as amount_price_gross,
                coalesce(psm.x_cnpj_cpf, '') as cnpj_cpf,
                coalesce(psm.x_label, brm.x_label) as label
            FROM rep_cf_inicial_bank as aml
                LEFT JOIN rep_cf_sale_purchase_journal as psm
                ON psm.x_full_reconcile_id = aml.x_full_reconcile_id
                LEFT JOIN rep_cf_s_reconcil_bank as brm
                ON brm.x_aml_id = aml.x_aml_id
                INNER JOIN account_move am ON am.id = aml.x_move_id
                INNER JOIN account_journal aj ON aj.id = aml.x_journal_id
            WHERE am.state = 'posted'

            UNION ALL

            SELECT DISTINCT
                bl.x_aml_id as id,
                bl.x_date as "date",
                'BANK_LINE' as line_type,
                bl.x_aml_id as move_line_id,
                bl.x_account_account_id as bank_account_id,
                bl.x_state as "state",
                bl.x_credit as credit,
                bl.x_debit as debit,
                bl.x_balance as balance,
                bl.x_bank_flow as bank_flow,
                bl.x_account_account_code as account_code,
                bl.x_name as "name",
                bl.x_full_reconcile_id as full_reconcile_id,
                bl.x_journal_id as journal_id,
                bl.x_company_id as company_id,
                0 as partner_id,
                0 as analytic_account_id,
                0 as move_id,
                DATE(NULL) as doc_date,
                bl.x_account_account_id as account_id,
                NULL as issuer,
                NULL as document_serie,
                NULL as document_number,
                0 as amount_price_gross,
                NULL as cnpj_cpf,
                NULL as label
            FROM rep_cf_bank_lines as bl
                INNER JOIN account_move am ON am.id = bl.x_move_id
            WHERE am.state = 'posted'
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self._cr.execute(
            "CREATE OR REPLACE VIEW %s AS (%s)", (AsIs(self._table), AsIs(query))
        )
