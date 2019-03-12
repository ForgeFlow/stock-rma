# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class RmaOrder(models.Model):
    _inherit = "rma.order"

    @api.multi
    def _compute_repair_count(self):
        for rma in self:
            repairs = rma.mapped('rma_line_ids.repair_ids')
            rma.repair_count = len(repairs)

    repair_count = fields.Integer(
        compute='_compute_repair_count', string='# of Repairs')

    @api.multi
    def action_view_repair_order(self):
        action = self.env.ref('repair.action_repair_order_tree')
        result = action.read()[0]
        repair_ids = self.mapped('rma_line_ids.repair_ids').ids
        result['domain'] = [('id', 'in', repair_ids)]
        return result
