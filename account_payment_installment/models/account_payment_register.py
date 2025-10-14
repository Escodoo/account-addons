# Copyright 2025 - TODAY, Wesley Oliveira <wesley.oliveira@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    installment_mode = fields.Boolean(default=False)
    installment_quantity = fields.Integer(default=1)

    def _create_payments(self):
        self.ensure_one()
        if not self.installment_mode or self.installment_quantity <= 1:
            return super()._create_payments()

        payments = self.env["account.payment"]
        amount = self.amount / self.installment_quantity
        start_date = self.payment_date

        for i in range(self.installment_quantity):
            wizard = self.copy(
                default={
                    "amount": amount,
                    "payment_date": start_date + relativedelta(months=i + 1),
                    "installment_mode": False,
                    "installment_quantity": 1,
                }
            )
            payments |= super(AccountPaymentRegister, wizard)._create_payments()

        return payments
