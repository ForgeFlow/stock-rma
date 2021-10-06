# Copyright 2021 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models
from odoo.tools import float_compare


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    lot_id = fields.Many2one(
        comodel_name="stock.production.lot",
        domain="[('id', 'in', valid_lots_ids)]",
    )
    valid_lots_ids = fields.One2many(
        comodel_name="stock.production.lot",
        compute="_compute_domain_lot_ids",
    )

    @api.depends("product_id")
    def _compute_domain_lot_ids(self):
        for rec in self:
            lots = rec.env["stock.production.lot"].search(
                [("product_id", "=", rec.product_id.id)]
            )
            if (
                lots
                and rec.type == "customer"
                and rec.product_id
                and rec.product_id.tracking != "none"
            ):
                valid_ids = self.env["stock.production.lot"]
                for quant in rec.product_id.stock_quant_ids:
                    if (
                        float_compare(quant.available_quantity, 0.0, precision_digits=2)
                        > 0
                        and quant.location_id.usage == "customer"
                        and quant.lot_id
                    ):
                        valid_ids |= quant.lot_id
                if valid_ids:
                    lots = valid_ids
            rec.valid_lots_ids = lots

    def _onchange_product_id(self):
        super()._onchange_product_id()
        return {"domain": {"lot_id": [("id", "in", self.valid_lots_ids)]}}
