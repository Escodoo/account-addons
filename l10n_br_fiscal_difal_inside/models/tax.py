# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import TAX_DOMAIN_ICMS_FCP


class Tax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    @api.model
    def _compute_icms(self, tax, taxes_dict, **kwargs):
        taxes_dict = super()._compute_icms(tax, taxes_dict, **kwargs)

        operation_line = kwargs.get("operation_line")
        if not operation_line.difal_inside_basis:
            return taxes_dict

        tax_dict = taxes_dict.get(tax.tax_domain, {})

        icms_dest_perc = tax_dict.get("icms_dest_perc", 0.00)
        icms_base = tax_dict.get("base", 0.00)
        if not icms_dest_perc or not icms_base:
            return taxes_dict

        icmsfcp_perc = self._get_difal_inside_fcp_percent(taxes_dict)

        divisor = 1 - ((icms_dest_perc + icmsfcp_perc) / 100)
        if divisor <= 0:
            return taxes_dict

        company = kwargs.get("company")
        currency = kwargs.get("currency", company.currency_id)

        icms_origin_perc = tax_dict.get("icms_origin_perc", 0.00)

        difal_icms_base = currency.round(icms_base / divisor)
        difal_value = currency.round(
            difal_icms_base * ((icms_dest_perc - icms_origin_perc) / 100)
        )

        difal_share_origin = tax_dict.get("difal_origin_perc", 0.00)
        difal_share_dest = tax_dict.get("difal_dest_perc", 100.00)

        tax_dict.update(
            {
                "icms_dest_base": difal_icms_base,
                "icms_origin_value": currency.round(
                    difal_value * difal_share_origin / 100
                ),
                "icms_dest_value": currency.round(difal_value * difal_share_dest / 100),
            }
        )

        return taxes_dict

    def _get_difal_inside_fcp_percent(self, taxes_dict):
        icmsfcp_perc = taxes_dict.get(TAX_DOMAIN_ICMS_FCP, {}).get(
            "percent_amount", 0.00
        )
        if not icmsfcp_perc:
            fcp_tax = self.filtered(lambda t: t.tax_domain == TAX_DOMAIN_ICMS_FCP)[:1]
            icmsfcp_perc = fcp_tax.percent_amount or 0.00
        return icmsfcp_perc
