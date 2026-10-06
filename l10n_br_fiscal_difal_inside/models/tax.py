# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    TAX_DOMAIN_ICMS,
    TAX_DOMAIN_ICMS_FCP,
)


class Tax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    @api.model
    def _compute_tax_sequence(self, taxes_dict, **kwargs):
        """Ensure ICMS FCP is computed after ICMS.

        The FCP base of an interstate operation is taken from the DIFAL base
        computed by ``_compute_icms``. If the ``compute_sequence`` of the tax
        groups puts ICMS FCP first, that base is not available yet and the FCP
        falls back to its own (not grossed up) base.
        """
        compute_sequence = super()._compute_tax_sequence(taxes_dict, **kwargs)

        operation_line = kwargs.get("operation_line")
        if not operation_line or not operation_line.difal_inside_basis:
            return compute_sequence

        icms_sequence = compute_sequence.get(TAX_DOMAIN_ICMS)
        fcp_sequence = compute_sequence.get(TAX_DOMAIN_ICMS_FCP)
        if icms_sequence is None or fcp_sequence is None:
            return compute_sequence

        if fcp_sequence <= icms_sequence:
            compute_sequence[TAX_DOMAIN_ICMS_FCP] = icms_sequence + 1

        return compute_sequence

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

        # The interstate ICMS shares the grossed up base.
        percent_amount = tax_dict.get("percent_amount", icms_origin_perc)
        tax_dict.update(
            {
                "base": difal_icms_base,
                "tax_value": currency.round(difal_icms_base * (percent_amount / 100)),
            }
        )

        return taxes_dict

    @api.model
    def _compute_icmsfcp(self, tax, taxes_dict, **kwargs):
        """Align the ICMS FCP base with the grossed up DIFAL base.

        The core already copies ``icms_dest_base`` into the FCP base for
        interstate operations, but only when the ICMS was computed first and
        when the DIFAL block was reached. This makes the inside basis mode
        deterministic regardless of the tax group compute sequence.
        """
        tax_dict = super()._compute_icmsfcp(tax, taxes_dict, **kwargs)

        operation_line = kwargs.get("operation_line")
        if not operation_line.difal_inside_basis:
            return tax_dict

        company = kwargs.get("company")
        partner = kwargs.get("partner")
        if company.state_id == partner.state_id:
            return tax_dict

        difal_base = taxes_dict.get(TAX_DOMAIN_ICMS, {}).get("icms_dest_base", 0.00)
        if not difal_base or tax_dict.get("base_type") != "percent":
            return tax_dict

        currency = kwargs.get("currency", company.currency_id)
        percent_amount = tax_dict.get("percent_amount", 0.00)

        tax_dict.update(
            {
                "base": difal_base,
                "tax_value": currency.round(difal_base * (percent_amount / 100)),
            }
        )

        return tax_dict

    def _get_difal_inside_fcp_percent(self, taxes_dict):
        icmsfcp_perc = taxes_dict.get(TAX_DOMAIN_ICMS_FCP, {}).get(
            "percent_amount", 0.00
        )
        if not icmsfcp_perc:
            fcp_tax = self.filtered(lambda t: t.tax_domain == TAX_DOMAIN_ICMS_FCP)[:1]
            icmsfcp_perc = fcp_tax.percent_amount or 0.00
        return icmsfcp_perc
