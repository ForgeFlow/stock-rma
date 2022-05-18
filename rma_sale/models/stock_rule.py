# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom,
                               location_id, name, origin, values, group_id):
        """ Pass sale line if defined """
        res = super()._get_stock_move_values(
            product_id, product_qty, product_uom, location_id, name, origin, values, group_id
        )
        if 'rma_line_id' in values:
            line = self.env['rma.order.line'].browse(values.get('rma_line_id'))
            if line.sale_line_id:
                res['sale_line_id'] = line.sale_line_id.id
        return res
