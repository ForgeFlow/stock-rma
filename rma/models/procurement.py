# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    rma_line_id = fields.Many2one(
        comodel_name='rma.order.line', string='RMA line',
        ondelete="set null",
    )

    def _get_stock_move_values(self, product_id, product_qty, product_uom,
                               location_id, name, origin, values, group_id):
        res = super(ProcurementRule, self)._get_stock_move_values(product_id,
                                                                  product_qty,
                                                                  product_uom,
                                                                  location_id,
                                                                  name, origin,
                                                                  values,
                                                                  group_id)
        if 'rma_line_id' in values:
            line = self.env['rma.order.line'].browse(values.get('rma_line_id'))
            res['rma_line_id'] = line.id
            if line.delivery_address_id:
                res['partner_id'] = line.delivery_address_id.id
            else:
                res['partner_id'] = line.rma_id.partner_id.id
            dest_loc = self.env["stock.location"].browse([
                res["location_dest_id"]])[0]
            if dest_loc.usage == "internal":
                res["price_unit"] = line.price_unit
        return res


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    rma_id = fields.Many2one(
        comodel_name='rma.order', string='RMA',
        ondelete="set null",
    )
    rma_line_id = fields.Many2one(
        comodel_name='rma.order.line', string='RMA line',
        ondelete="set null",
    )
