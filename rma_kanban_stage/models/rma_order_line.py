# Copyright 2019 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import api, fields, models


class RmaOrderLine(models.Model):
    _name = 'rma.order.line'
    _inherit = ['rma.order.line', 'base.kanban.abstract']

    user_id = fields.Many2one(
        comodel_name='res.users', related='assigned_to'
    )

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = default or {}
        stage = self.stage_id.search([], order="sequence asc", limit=1)
        default.update({'stage_id': stage.id})
        return super(RmaOrderLine, self).copy(default=default)
