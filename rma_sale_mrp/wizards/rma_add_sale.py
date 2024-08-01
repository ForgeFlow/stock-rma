# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class RmaAddSale(models.TransientModel):
    _inherit = "rma_add_sale"

    def _create_from_move_line(self, line):
        phantom_bom = line.move_ids.bom_line_id.bom_id.filtered(
            lambda bom: bom.type == "phantom"
        )
        if phantom_bom and not line.company_id.rma_add_component_from_sale:
            return False
        return super()._create_from_move_line(line)
