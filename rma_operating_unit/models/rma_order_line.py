# © 2017-19 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class RmaOrderLine(models.Model):

    _inherit = "rma.order.line"

    @api.model
    def _default_operating_unit(self):
        if self.rma_id.operating_unit_id:
            return self.rma_id.operating_unit_id.id
        return self.env.user.default_operating_unit_id

    operating_unit_id = fields.Many2one(
        comodel_name='operating.unit',
        string='Operating Unit',
        default=_default_operating_unit,
    )
