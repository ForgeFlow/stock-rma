# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import api, fields, models
from openerp.addons import decimal_precision as dp


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.one
    def _compute_purchase_count(self):
        purchase_list = []
        for procurement_id in self.procurement_ids:
            if procurement_id.purchase_id and procurement_id.purchase_id.id:
                purchase_list.append(procurement_id.purchase_id.id)
        self.purchase_count = len(list(set(purchase_list)))

    @api.one
    @api.depends('procurement_ids.purchase_line_id')
    def _get_purchase_order_lines(self):
        purchase_list = []
        for procurement_id in self.procurement_ids:
            if procurement_id.purchase_line_id and \
                    procurement_id.purchase_line_id.id:
                purchase_list.append(procurement_id.purchase_line_id.id)
        self.purchase_order_line_ids = [(6, 0, purchase_list)]

    @api.one
    @api.depends('procurement_ids.purchase_line_id')
    def _compute_qty_purchased(self):
        self.qty_purchased = self._get_rma_purchased_qty()

    purchase_count = fields.Integer(compute=_compute_purchase_count,
                                    string='# of Purchases', copy=False,
                                    default=0)
    purchase_order_line_id = fields.Many2one('purchase.order.line',
                                             string='Origin Purchase Line',
                                             ondelete='restrict')
    purchase_order_line_ids = fields.Many2many(
        'purchase.order.line', 'purchase_line_rma_line_rel',
        'rma_order_line_id', 'purchase_order_line_id',
        string='Purchase Order Lines', compute=_get_purchase_order_lines)

    qty_purchased = fields.Float(
        string='Qty Purchased', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_purchased,
        store=True)

    @api.multi
    def action_view_purchase_order(self):
        action = self.env.ref('purchase.purchase_rfq')
        result = action.read()[0]
        order_ids = []
        for procurement_id in self.procurement_ids:
            order_ids.append(procurement_id.purchase_id.id)
        result['domain'] = [('id', 'in', order_ids)]
        return result

    @api.multi
    def _get_rma_purchased_qty(self):
        self.ensure_one()
        qty = 0.0
        for procurement_id in self.procurement_ids:
            purchase_line = procurement_id.purchase_line_id
            if self.type == 'supplier':
                qty += purchase_line.product_qty
            else:
                qty = 0.0
        return qty
