# Copyright 2026 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import unicodedata

from odoo import api, models

OFX_ENCODINGS = ("utf-8", "cp1252")


class AccountStatementImport(models.TransientModel):

    _inherit = "account.statement.import"

    @api.model
    def _sanitize_ofx_accents(self, data_file):
        """Return the OFX file content with accented characters replaced by
        their unaccented ASCII equivalent (e.g. SAIDA instead of SAÍDA)."""
        for encoding in OFX_ENCODINGS:
            try:
                content = data_file.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            # latin-1 maps every possible byte, so it never raises.
            content = data_file.decode("latin-1")

        decomposed = unicodedata.normalize("NFKD", content)
        unaccented = "".join(
            char for char in decomposed if not unicodedata.combining(char)
        )
        return unaccented.encode("ascii", "ignore")

    @api.model
    def _check_ofx(self, data_file):
        return super()._check_ofx(self._sanitize_ofx_accents(data_file))
