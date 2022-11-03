# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    rma_line_id = fields.Many2one("rma.order.line", string="RMA order Line")

    is_rma_scrap = fields.Boolean(
        string="Is RMA Scrap",
        default=False,
        copy=False,
        help="This Stock Move has been created from a Scrap operation in " "the RMA.",
    )

    def do_scrap(self):
        super(StockScrap, self).do_scrap()
        if self.is_rma_scrap:
            self.move_id.is_rma_scrap = True
            self.rma_line_id.move_ids |= self.move_id
