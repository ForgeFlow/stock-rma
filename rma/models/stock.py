# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def action_assign(self):
        for picking in self:
            for move in picking.move_lines:
                if len(move.rma_line_id):
                    if move.state in ('confirmed', 'waiting', 'assigned') \
                            and move.location_id.usage in (
                                'supplier', 'customer'):
                        move.force_assign()
        return super(StockPicking, self).action_assign()


class StockMove(models.Model):

    _inherit = "stock.move"

    rma_line_id = fields.Many2one('rma.order.line', string='RMA',
                                  ondelete='restrict')

    @api.model
    def create(self, vals):
        if vals.get('procurement_id', False):
            procurement = self.env['procurement.order'].browse(
                vals['procurement_id'])
            if procurement.rma_line_id and procurement.rma_line_id.id:
                vals['rma_line_id'] = procurement.rma_line_id.id
        return super(StockMove, self).create(vals)
