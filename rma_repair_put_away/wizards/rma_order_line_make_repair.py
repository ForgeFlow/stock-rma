# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class RmaLineMakeRepair(models.TransientModel):
    _inherit = "rma.order.line.make.repair"

    def create_repair_procurement_condition_applies(self, rma_line, repair):
        res = super().create_repair_procurement_condition_applies(rma_line, repair)
        if rma_line.operation_id.put_away_location_id:
            return rma_line.operation_id.put_away_location_id != repair.location_id
        return res
