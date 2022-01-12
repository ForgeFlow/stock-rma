# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import fields, models


class RmaOperation(models.Model):

    _inherit = "rma.operation"

    receipt_policy = fields.Selection(
        selection_add=[
            ("prepaid_invoice_ordered", "Prepaid Service Invoice - Ordered"),
            ("prepaid_invoice_delivered", "Prepaid Service Invoice - Delivered"),
        ],
        ondelete={
            "prepaid_invoice_ordered": lambda recs: recs.write(
                {"receipt_policy": "ordered"}
            ),
            "prepaid_invoice_delivered": lambda recs: recs.write(
                {"receipt_policy": "delivered"}
            ),
        },
    )
