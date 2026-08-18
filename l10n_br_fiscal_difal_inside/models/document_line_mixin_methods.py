# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_FCP,
)


class DocumentLineMixinMethods(models.AbstractModel):
    _inherit = "l10n_br_fiscal.document.line.mixin.methods"

    def _compute_taxes(self, taxes, cst=None):
        """Recompose the DIFAL and FCP bases on every computation of the line.

        The taxes are computed again by ``_update_fiscal_taxes`` when the
        invoice is saved, and not only by the onchanges.
        """
        compute_result = super()._compute_taxes(taxes, cst=cst)
        return self._difal_inside_recompose(compute_result)

    def _difal_inside_recompose(self, compute_result):
        self.ensure_one()

        if not self.fiscal_operation_line_id.difal_inside_basis:
            return compute_result

        computed_taxes = compute_result.get("taxes", {})
        icms_dict = computed_taxes.get(TAX_DOMAIN_ICMS)
        if not icms_dict:
            return compute_result

        fcp_dict = computed_taxes.get(TAX_DOMAIN_ICMS_FCP, {})
        currency = self.company_id.currency_id

        # The gross up starts from the ICMS base, which is not touched here,
        # so computing the taxes twice keeps the same amounts.
        amounts = self.env["l10n_br_fiscal.tax"]._difal_inside_amounts(
            icms_base=icms_dict.get("base", 0.00),
            icms_dest_perc=icms_dict.get("icms_dest_perc", 0.00),
            icms_origin_perc=icms_dict.get("icms_origin_perc", 0.00),
            icmsfcp_perc=fcp_dict.get("percent_amount", 0.00),
            currency=currency,
            difal_share_origin=icms_dict.get("difal_origin_perc", 0.00),
            difal_share_dest=icms_dict.get("difal_dest_perc", 100.00),
        )
        if not amounts:
            return compute_result

        icms_dict.update(
            {
                "icms_dest_base": amounts["icms_dest_base"],
                "icms_origin_value": amounts["icms_origin_value"],
                "icms_dest_value": amounts["icms_dest_value"],
            }
        )

        if fcp_dict.get("base_type") == "percent":
            amount_key = (
                "amount_included"
                if fcp_dict.get("tax_include")
                else "amount_not_included"
            )
            compute_result[amount_key] = currency.round(
                compute_result.get(amount_key, 0.00)
                + amounts["icmsfcp_value"]
                - fcp_dict.get("tax_value", 0.00)
            )
            fcp_dict.update(
                {
                    "base": amounts["icmsfcp_base"],
                    "tax_value": amounts["icmsfcp_value"],
                }
            )

        return compute_result
