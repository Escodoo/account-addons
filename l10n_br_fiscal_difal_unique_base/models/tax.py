# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    FINAL_CUSTOMER_NO,
    FINAL_CUSTOMER_YES,
    NFE_IND_IE_DEST_9,
)
from odoo.addons.l10n_br_fiscal.constants.icms import ICMS_DIFAL_DOUBLE_BASE


class Tax(models.Model):
    _inherit = "l10n_br_fiscal.tax"

    @api.model
    def _compute_icms(self, tax, taxes_dict, **kwargs):
        taxes_dict = super()._compute_icms(tax, taxes_dict, **kwargs)

        tax_dict = taxes_dict.get(tax.tax_domain, {})
        partner = kwargs.get("partner")
        ind_final = kwargs.get("ind_final", FINAL_CUSTOMER_NO)

        if (
            not tax_dict.get("icms_dest_base")
            or not partner
            or partner.ind_ie_dest != NFE_IND_IE_DEST_9
            or ind_final != FINAL_CUSTOMER_YES
            or partner.state_id.code not in ICMS_DIFAL_DOUBLE_BASE
        ):
            return taxes_dict

        company = kwargs.get("company")
        currency = kwargs.get("currency", company.currency_id)

        icms_base = tax_dict.get("base", 0.00)
        icms_dest_perc = tax_dict.get("icms_dest_perc", 0.00)
        icms_origin_value = tax_dict.get("tax_value", 0.00)

        difal_icms_base = icms_base
        icms_dest_value = currency.round(icms_base * (icms_dest_perc / 100))
        difal_value = icms_dest_value - icms_origin_value

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
