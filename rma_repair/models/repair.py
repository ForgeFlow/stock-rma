# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    rma_line_id = fields.Many2one(
        comodel_name='rma.order.line', string='RMA', ondelete='restrict',
    )
    under_warranty = fields.Boolean(
        related='rma_line_id.under_warranty', readonly=False,
    )
    invoice_status = fields.Selection(related='invoice_id.state')
