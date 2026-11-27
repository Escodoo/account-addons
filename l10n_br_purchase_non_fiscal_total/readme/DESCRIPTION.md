With the Brazilian localization (`l10n_br_purchase`), a purchase order without a fiscal
operation shows a zero total, because the order total is rebuilt from the fiscal lines.

This module keeps the regular total (the sum of the line totals) on purchase orders that
have no fiscal operation. Orders with a fiscal operation are not changed.
