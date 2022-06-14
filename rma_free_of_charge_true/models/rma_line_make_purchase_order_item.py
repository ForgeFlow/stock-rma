from odoo import fields, models


class RmaLineMakePurchaseOrderItem(models.TransientModel):
    _inherit = "rma.order.line.make.purchase.order.item"

    free_of_charge = fields.Boolean(default="True")
