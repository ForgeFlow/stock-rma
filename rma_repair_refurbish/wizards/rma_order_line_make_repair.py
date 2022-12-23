# Copyright 2020-22 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class RmaLineMakeRepair(models.TransientModel):
    _inherit = "rma.order.line.make.repair"

    @api.model
    def _prepare_item(self, line):
        res = super(RmaLineMakeRepair, self)._prepare_item(line)
        if line.product_id.refurbish_product_id:
            to_refurbish = True
            refurbish_product_id = line.product_id.refurbish_product_id.id
        else:
            to_refurbish = refurbish_product_id = False
        res["to_refurbish"] = to_refurbish
        if refurbish_product_id:
            res["refurbish_product_id"] = refurbish_product_id
        res["location_dest_id"] = (
            line.operation_id.repair_location_dest_id.id or line.location_id.id
        )
        return res


class RmaLineMakeRepairItem(models.TransientModel):
    _inherit = "rma.order.line.make.repair.item"

    @api.onchange("to_refurbish")
    def _onchange_to_refurbish(self):
        if self.to_refurbish:
            self.refurbish_product_id = self.product_id.refurbish_product_id
        else:
            self.refurbish_product_id = False

    location_dest_id = fields.Many2one(
        comodel_name="stock.location", string="Destination location", required=True
    )
    to_refurbish = fields.Boolean(string="To Refurbish?")
    refurbish_product_id = fields.Many2one(
        comodel_name="product.product", string="Refurbished Product"
    )

    def _prepare_repair_order(self, rma_line):
        res = super(RmaLineMakeRepairItem, self)._prepare_repair_order(rma_line)
        location_dest = (
            self.location_dest_id
            if not self.to_refurbish
            else rma_line.product_id.property_stock_refurbish
        )
        refurbish_location_dest_id = (
            self.location_dest_id.id if self.to_refurbish else False
        )
        res["location_dest_id"] = location_dest.id
        res["refurbish_location_dest_id"] = refurbish_location_dest_id
        res["to_refurbish"] = self.to_refurbish
        return res
