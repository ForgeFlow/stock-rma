# Copyright (C) 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class RmaMakePicking(models.TransientModel):

    _inherit = "rma_make_picking.wizard"

    def _create_picking(self):
        res = super()._create_picking()
        for line in self.mapped("item_ids.line_id").filtered(
            lambda x: x.operation_id.default_carrier_id
        ):
            pickings = line._get_out_pickings().filtered(lambda x: not x.carrier_id)
            pickings.write({"carrier_id": line.operation_id.default_carrier_id.id})
        return res
