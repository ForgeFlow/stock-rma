# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.depends('sale_line_ids', 'sale_type', 'sales_count',
                 'sale_line_ids.state')
    @api.multi
    def _compute_qty_to_sell(self):
        for rec in self:
            if rec.sale_type == 'no':
                rec.qty_to_sell = 0.0
            elif rec.sale_type == 'ordered':
                qty = self._get_rma_sold_qty()
                rec.qty_to_sell = self.product_qty - qty
            elif rec.sale_type == 'received':
                qty = self._get_rma_sold_qty()
                rec.qty_to_sell = self.qty_received - qty
            else:
                rec.qty_to_sell = 0.0

    @api.depends('sale_line_ids', 'sale_type', 'sales_count',
                 'sale_line_ids.state')
    def _compute_qty_sold(self):
        self.qty_sold = self._get_rma_sold_qty()

    @api.multi
    def _compute_sales_count(self):
        for line in self:
            sales = line.mapped('sale_line_ids.order_id')
            line.sales_count = len(sales)

    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line', string='Originating Sales Order Line',
        ondelete='restrict', copy=False,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    sale_id = fields.Many2one(
        string="Source Sales Order", related='sale_line_id.order_id',
        readonly=True,
    )
    sale_line_ids = fields.One2many(
        comodel_name='sale.order.line', inverse_name='rma_line_id',
        string='Sales Order Lines', readonly=True,
        states={'draft': [('readonly', False)]}, copy=False)
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
    sale_type = fields.Selection(selection=[
        ('no', 'Not required'), ('ordered', 'Based on Ordered Quantities'),
        ('received', 'Based on Received Quantities')],
        string="Sale Policy", default='no', required=True)
    sales_count = fields.Integer(
        compute=_compute_sales_count, string='# of Sales')

    @api.multi
    def _prepare_rma_line_from_sale_order_line(self, line):
        self.ensure_one()
        if not self.type:
            self.type = self._get_default_type()
        operation = line.product_id.rma_customer_operation_id
        if not operation:
            operation = line.product_id.categ_id.rma_customer_operation_id
        if not operation:
            operation = self.env['rma.operation'].search(
                [('type', '=', self.type)], limit=1)
            if not operation:
                raise ValidationError(_("Please define an operation first"))
        if not operation.in_route_id or not operation.out_route_id:
            route = self.env['stock.location.route'].search(
                [('rma_selectable', '=', True)], limit=1)
            if not route:
                raise ValidationError(_("Please define an RMA route"))
        if not operation.in_warehouse_id or not operation.out_warehouse_id:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id),
                 ('lot_rma_id', '!=', False)], limit=1)
            if not warehouse:
                raise ValidationError(_(
                    "Please define a warehouse with a default RMA location."))
        data = {
            'product_id': line.product_id.id,
            'origin': line.order_id.name,
            'uom_id': line.product_uom.id,
            'operation_id': operation.id,
            'product_qty': line.product_uom_qty,
            'delivery_address_id': line.order_id.partner_id.id,
            'invoice_address_id': line.order_id.partner_id.id,
            'price_unit': line.currency_id.compute(
                line.price_unit, line.currency_id, round=False),
            'in_route_id': operation.in_route_id.id or route.id,
            'out_route_id': operation.out_route_id.id or route.id,
            'receipt_policy': operation.receipt_policy,
            'location_id': (operation.location_id.id or
                            operation.in_warehouse_id.lot_rma_id.id or
                            warehouse.lot_rma_id.id),
            'refund_policy': operation.refund_policy,
            'delivery_policy': operation.delivery_policy,
            'in_warehouse_id': operation.in_warehouse_id.id or warehouse.id,
            'out_warehouse_id': operation.out_warehouse_id.id or warehouse.id,
        }
        return data

    @api.onchange('sale_line_id')
    def _onchange_sale_line_id(self):
        if not self.sale_line_id:
            return
        data = self._prepare_rma_line_from_sale_order_line(
            self.sale_line_id)
        self.update(data)
        self._remove_other_data_origin('sale_line_id')

    @api.multi
    def _remove_other_data_origin(self, exception):
        res = super(RmaOrderLine, self)._remove_other_data_origin(exception)
        if not exception == 'sale_line_id':
            self.sale_line_id = False
        return res

    @api.multi
    @api.constrains('sale_line_id', 'partner_id')
    def _check_sale_partner(self):
        for rec in self:
            if (rec.sale_line_id and rec.sale_line_id.order_id.partner_id !=
                    rec.partner_id):
                raise ValidationError(_(
                    "RMA customer and originating sales order line customer "
                    "doesn't match."))

    @api.multi
    def action_view_sale_order(self):
        action = self.env.ref('sale.action_quotations')
        result = action.read()[0]
        order_ids = self.mapped('sale_line_ids.order_id').ids
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
