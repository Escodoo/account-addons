# Copyright 2024 - TODAY, Kaynnan Lemes <kaynnan.lemes@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class AccountMove(models.Model):

    _inherit = "account.move"

    is_advance_move = fields.Boolean(
        string="Advance Move",
    )

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
