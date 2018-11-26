# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class MrpRepair(models.Model):
    _inherit = "mrp.repair"

    rma_line_id = fields.Many2one(
        comodel_name='rma.order.line', string='RMA', ondelete='restrict',
    )
    under_warranty = fields.Boolean(
        related='rma_line_id.under_warranty',
    )
