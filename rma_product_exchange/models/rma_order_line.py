# Copyright 2024 Akretion
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    new_product_id = fields.Many2one(
        comodel_name="product.product",
        tracking=True,
        help="The new product selected will be shipped "
        "instead of the product initially ordered.",
    )
    product_exchange = fields.Boolean(related="operation_id.product_exchange")

    @api.constrains("new_product_id")
    def _check_new_product_id(self):
        for record in self:
            if (
                record.new_product_id
                and record.new_product_id.uom_id != record.product_id.uom_id
            ):
                raise ValidationError(
                    _(
                        "The selected replacement product must "
                        "have the same unit of measurement as the initial product !"
                    )
                )
