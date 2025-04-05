# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models


class AccountMove(models.Model):

    _inherit = "account.move"
    advance_invoice = fields.Boolean(compute="_compute_advance_invoice")

    @api.depends(
        "payment_state",
        "partner_id",
        "line_ids",
        "line_ids.account_id",
        "line_ids.account_id.account_type",
        "line_ids.amount_residual",
    )
    def _compute_advance_invoice(self):
        """Compute whether this invoice has related advance payments available."""
        prepayment_account_type = "asset_prepayments"

        for record in self:
            record.advance_invoice = False

            if not record.partner_id:
                continue

            domain = [
                ("move_id.payment_state", "=", "paid"),
                ("partner_id", "=", record.partner_id.id),
                ("account_id.account_type", "=", prepayment_account_type),
                ("account_id.reconcile", "=", True),
            ]

            if record.move_type == "in_invoice":
                domain.append(("amount_residual", ">", 0.0))
            elif record.move_type == "out_invoice":
                domain.append(("amount_residual", "<", 0.0))
            else:
                continue  # Skip unsupported types

            has_advance = self.env["account.move.line"].search_count(domain) > 0
            record.advance_invoice = has_advance

    def action_compensate_advance(self):

        return {
            "name": _("Compensate Advance"),
            "res_model": "account.compensate.advance.journal",
            "view_mode": "form",
            "context": {
                "active_model": "account.move",
                "active_ids": self.ids,
                "default_move_type": self.env.context.get("default_move_type"),
            },
            "target": "new",
            "type": "ir.actions.act_window",
        }
