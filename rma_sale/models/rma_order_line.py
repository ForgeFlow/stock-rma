# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import api, fields, models
from openerp.addons import decimal_precision as dp


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.one
    @api.depends('sale_line_ids', 'sale_type', 'sales_count',
                 'sale_line_ids.state')
    def _compute_qty_to_sell(self):
        if self.sale_type == 'no':
            self.qty_to_sell = 0.0
        elif self.sale_type == 'ordered':
            qty = self._get_rma_sold_qty()
            self.qty_to_sell = self.product_qty - qty
        elif self.sale_type == 'received':
            qty = self._get_rma_sold_qty()
            self.qty_to_sell = self.qty_received - qty
        else:
            self.qty_to_sell = 0.0

    @api.one
    @api.depends('sale_line_ids', 'sale_type', 'sales_count',
                 'sale_line_ids.state')
    def _compute_qty_sold(self):
        self.qty_sold = self._get_rma_sold_qty()

    @api.one
    def _compute_sales_count(self):
        sales_list = []
        for sale_order_line in self.sale_line_ids:
            sales_list.append(sale_order_line.order_id.id)
        self.sales_count = len(list(set(sales_list)))

    sale_line_id = fields.Many2one(comodel_name='sale.order.line',
                                   string='Originating Sales Order Line',
                                   ondelete='restrict')
    sale_line_ids = fields.One2many(comodel_name='sale.order.line',
                                    inverse_name='rma_line_id',
                                    string='Sales Order Lines', readonly=True,
                                    states={'draft': [('readonly', False)]},
                                    copy=False)
    qty_to_sell = fields.Float(
        string='Qty To Sell', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_to_sell,
        store=True)

    qty_sold = fields.Float(
        string='Qty Sold', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_sold,
        store=True)

    sale_type = fields.Selection([
        ('no', 'Not required'), ('ordered', 'Based on Ordered Quantities'),
        ('received', 'Based on Received Quantities')],
        string="Sale Policy", default='no', required=True)

    sales_count = fields.Integer(compute=_compute_sales_count,
                                 string='# of Sales', copy=False, default=0)

    @api.multi
    def action_view_sale_order(self):
        action = self.env.ref('sale.action_quotations')
        result = action.read()[0]
        order_ids = []
        for sale_line in self.sale_line_ids:
            order_ids.append(sale_line.order_id.id)
        result['domain'] = [('id', 'in', order_ids)]
        return result

    @api.multi
    def _get_rma_sold_qty(self):
        self.ensure_one()
        qty = 0.0
        for sale_line in self.sale_line_ids.filtered(
                lambda p: p.state not in ('draft', 'sent', 'cancel')):
            qty += sale_line.product_uom_qty
        return qty
