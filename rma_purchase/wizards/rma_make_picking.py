# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class RmaMakePicking(models.TransientModel):
    _inherit = "rma_make_picking.wizard"

    def _prepare_item(self, line):
        res = super()._prepare_item(line)
        res["purchase_order_line_id"] = line.purchase_order_line_id.id
        return res


class RmaMakePickingItem(models.TransientModel):
    _inherit = "rma_make_picking.wizard.item"

    purchase_order_line_id = fields.Many2one(
        "purchase.order.line", string="Purchase Line"
    )
