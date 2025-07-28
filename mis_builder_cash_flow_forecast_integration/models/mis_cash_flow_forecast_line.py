# Copyright 2022 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MisCashFlowForecastLine(models.Model):

    _inherit = "mis.cash_flow.forecast_line"

    res_id = fields.Integer(string="Resource ID")
    res_model_id = fields.Many2one("ir.model", "Document Model", ondelete="cascade")
    res_model = fields.Char(
        "Document Model Name", related="res_model_id.model", readonly=True
    )

    parent_res_id = fields.Integer(string="Parent Resource ID")
    parent_res_model_id = fields.Many2one(
        "ir.model", "Parent Document Model", ondelete="cascade"
    )
    parent_res_model = fields.Char(
        "Parent Document Model Name",
        related="parent_res_model_id.model",
        readonly=True,
    )

    def action_open_document_related(self):
        """
        Open the related document associated with the record.

        Returns:
            action (dict): The action to open the related document.
                If the record has a valid res_model and res_id, it returns the form
                view action of the related document.
                Otherwise, it returns False.
        """
        if self.res_model and self.res_id:
            return self.env[self.res_model].browse(self.res_id).get_formview_action()
        return False

    def action_open_parent_document_related(self):
        """
        Open the parent document related to the current record.

        If the parent_res_model and parent_res_id are set, it retrieves the parent record
        and returns the action to open its form view. Otherwise, it returns False.

        :return: The action to open the parent record's form view or False if no parent
        record is found.
        :rtype: dict or bool
        """
        if self.parent_res_model and self.parent_res_id:
            return (
                self.env[self.parent_res_model]
                .browse(self.parent_res_id)
                .get_formview_action()
            )
        return False
