# © 2017-19 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RmaOrder(models.Model):

    _inherit = "rma.order"

    @api.multi
    @api.constrains('rma_line_ids', 'rma_line_ids.operating_unit_id')
    def _check_operating_unit(self):
        for rma in self:
            bad_lines = rma.rma_line_ids.filtered(
                lambda l: l.operating_unit_id != rma.operating_unit_id)
            if bad_lines:
                raise ValidationError(
                    _('The operating unit of the rma lines have to match the'
                      ' one of the group'))
        return True

    @api.model
    def _default_operating_unit(self):
        return self.env.user.default_operating_unit_id

    operating_unit_id = fields.Many2one(
        comodel_name='operating.unit',
        string='Operating Unit',
        default=_default_operating_unit,
    )
