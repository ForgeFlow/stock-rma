# Copyright (C) 2024 Akretion
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class RmaMakePicking(models.TransientModel):
    _inherit = "rma_make_picking.wizard"

    @api.returns("rma.order.line")
    def _prepare_item(self, line):
        values = super()._prepare_item(line)
        if (
            self.env.context.get("picking_type") == "outgoing"
            and line.product_exchange
            and line.new_product_id
        ):
            values["product_id"] = line.new_product_id.id
        return values

    @api.model
    def _create_procurement(self, item, picking_type):
        if self.env.context.get("picking_type") == "outgoing":
            self = self.with_context(rma_item=item)
        return super()._create_procurement(item, picking_type)

    @api.model
    def _get_product(self, item):
        product = super()._get_product(item)
        if (
            self.env.context.get("picking_type") == "outgoing"
            and item.line_id.product_exchange
            and item.line_id.new_product_id
        ):
            product = item.line_id.new_product_id
        return product
