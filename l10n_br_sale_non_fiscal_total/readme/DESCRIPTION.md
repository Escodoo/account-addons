With the Brazilian localization (`l10n_br_sale`), a sale order without a fiscal operation
(for example, a rental or an internal order that does not issue a fiscal document) shows a
zero total, because the order total is rebuilt from the fiscal lines.

This module keeps the regular total (the sum of the line totals) on sale orders that have no
fiscal operation. Orders with a fiscal operation are not changed.
