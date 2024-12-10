To use this module, you need to:

- Create KPIs for checking results using the name `check`, this KPIs will be invisible when export to PDF.
- Check the "Is Profit or Loss?" field.
- Fill the description with the key word `Lucro` (Profit).
- This word will change to `Prejuizo` (Loss) when the sum of the row is negative.
- When select the `hide_period_labels` in the instance, the column labels don't will be visible in PDF exportations.
- When you use the `$date_to` keyword in the kpi description, it will be changed to de `date_to` field of the report istance.
- It will works only if there is only one instance with the report model and the instance don't have the `comparison_mode` enabled.
