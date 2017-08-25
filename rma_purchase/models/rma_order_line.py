# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import api, fields, models
from openerp.addons import decimal_precision as dp


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.multi
    def _compute_purchase_count(self):
        for rec in self:
            purchase_list = []
            for procurement_id in rec.procurement_ids:
                if procurement_id.purchase_id and \
                        procurement_id.purchase_id.id:
                    purchase_list.append(procurement_id.purchase_id.id)
            rec.purchase_count = len(list(set(purchase_list)))

    @api.multi
    @api.depends('procurement_ids.purchase_line_id')
    def _get_purchase_order_lines(self):
        for rec in self:
            purchase_list = []
            for procurement_id in rec.procurement_ids:
                if procurement_id.purchase_line_id and \
                        procurement_id.purchase_line_id.id:
                    purchase_list.append(procurement_id.purchase_line_id.id)
            rec.purchase_order_line_ids = [(6, 0, purchase_list)]

    @api.multi
    @api.depends('procurement_ids.purchase_line_id')
    def _compute_qty_purchased(self):
        for rec in self:
            rec.qty_purchased = rec._get_rma_purchased_qty()

    purchase_count = fields.Integer(
        compute='_compute_purchase_count', string='# of Purchases')
    purchase_order_line_id = fields.Many2one(
        comodel_name='purchase.order.line', string='Origin Purchase Line',
        ondelete='restrict')
    purchase_order_line_ids = fields.Many2many(
        comodel_name='purchase.order.line',
        relation='purchase_line_rma_line_rel',
        column1='rma_order_line_id', column2='purchase_order_line_id',
        string='Purchase Order Lines', compute='_get_purchase_order_lines')
    qty_purchased = fields.Float(
        string='Qty Purchased', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute='_compute_qty_purchased', store=True)

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
