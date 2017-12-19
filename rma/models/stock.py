# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def action_assign(self):
        """When you try to bring back a product from a customer location,
        it may happen that there is no quants available to perform the
        picking."""
        res = super(StockPicking, self).action_assign()
        for picking in self:
            for move in picking.move_lines:
                if (move.rma_line_id and move.state == 'confirmed' and
                        move.location_id.usage == 'customer'):
                    move.force_assign()
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    rma_line_id = fields.Many2one('rma.order.line', string='RMA line',
                                  ondelete='restrict')

    @api.model
    def create(self, vals):
        if vals.get('procurement_id'):
            procurement = self.env['procurement.order'].browse(
                vals['procurement_id'])
            if procurement.rma_line_id:
                vals['rma_line_id'] = procurement.rma_line_id.id
        return super(StockMove, self).create(vals)
