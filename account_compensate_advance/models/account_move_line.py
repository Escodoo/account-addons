# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# flake8: noqa: B950

import locale

from odoo import _, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    def name_get(self):
        """
        Override the name_get method to customize the display name of records based on the context.
        """
        context = self._context or {}
        locale.setlocale(locale.LC_ALL, self.env.user.lang)

        # Customize name display for 'advance_id' based on context
        if "advance_id_name_get" in context and context["advance_id_name_get"]:
            result = []
            balance_str = _("Balance")
            for rec in self:
                # Format name with localized date, total, and balance
                name = (
                    f"{rec.name} | "
                    f"{_('Date')}: {rec.move_id.date.strftime('%x')} | "
                    f"{_('Total')}: {locale.format_string('%.2f', abs(rec.price_total), grouping=True)} | "
                    f"{balance_str}: {locale.format_string('%.2f', abs(rec.amount_residual), grouping=True)}"
                )
                result.append((rec.id, name))
            return result

        # Customize name display for 'line_id' based on context
        if "line_id_name_get" in context and context["line_id_name_get"]:
            result = []
            for rec in self:
                # Format name with localized date and total
                name = (
                    f"{rec.name or rec.move_id.name} | "
                    f"{_('Date')}: {rec.date_maturity.strftime('%x')} | "
                    f"{_('Total')}: {locale.format_string('%.2f', abs(rec.price_total), grouping=True)}"
                )
                result.append((rec.id, name))
            return result

        # Call super method to get default name display
        return super().name_get()
