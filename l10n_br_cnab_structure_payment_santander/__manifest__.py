# Copyright 2024 - TODAY, Escodoo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# pylint:disable=file-not-used
{
    "name": "CNAB Structure - Santander",
    "summary": """
        This module extends the l10n_br_cnab_structure to implement the Santander
        data layout. It allows defining the structure for generating the CNAB
        file, used to exchange information with Brazilian banks.
    """,
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Escodoo",
    "website": "https://github.com/Escodoo/account-addons",
    "depends": ["l10n_br_cnab_structure"],
    "post_init_hook": "post_init_hook",
    "external_dependencies": {"python": ["pyyaml", "unidecode"]},
}
