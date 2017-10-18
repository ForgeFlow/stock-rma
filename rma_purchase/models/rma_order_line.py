# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError
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
        compute='_compute_purchase_count', string='# of Purchases',
    )
    purchase_order_line_id = fields.Many2one(
        comodel_name='purchase.order.line', string='Originating Purchase Line',
        ondelete='restrict',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    purchase_order_line_ids = fields.Many2many(
        comodel_name='purchase.order.line',
        relation='purchase_line_rma_line_rel',
        column1='rma_order_line_id', column2='purchase_order_line_id',
        string='Purchase Order Lines', compute='_get_purchase_order_lines',
    )
    qty_purchased = fields.Float(
        string='Qty Purchased', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute='_compute_qty_purchased', store=True,
    )

    @api.multi
    def _prepare_rma_line_from_po_line(self, line):
        self.ensure_one()
        if not self.type:
            self.type = self._get_default_type()
        if self.type == 'customer':
            operation = line.product_id.rma_customer_operation_id or \
                line.product_id.categ_id.rma_customer_operation_id
        else:
            operation = line.product_id.rma_supplier_operation_id or \
                line.product_id.categ_id.rma_supplier_operation_id
        if not operation:
            operation = self.env['rma.operation'].search(
                [('type', '=', self.type)], limit=1)
            if not operation:
                raise ValidationError(_("Please define an operation first"))

        if not operation.in_route_id or not operation.out_route_id:
            route = self.env['stock.location.route'].search(
                [('rma_selectable', '=', True)], limit=1)
            if not route:
                raise ValidationError(_("Please define a rma route."))

        if not operation.in_warehouse_id or not operation.out_warehouse_id:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id),
                 ('lot_rma_id', '!=', False)], limit=1)
            if not warehouse:
                raise ValidationError(_(
                    "Please define a warehouse with a default rma location."))

        data = {
            'product_id': line.product_id.id,
            'origin': line.order_id.name,
            'uom_id': line.product_uom.id,
            'operation_id': operation.id,
            'product_qty': line.product_qty,
            'price_unit': line.currency_id.compute(
                line.price_unit, line.currency_id, round=False),
            'in_route_id': operation.in_route_id.id or route,
            'out_route_id': operation.out_route_id.id or route,
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

    @api.onchange('purchase_order_line_id')
    def _onchange_purchase_order_line_id(self):
        if not self.purchase_order_line_id:
            return
        data = self._prepare_rma_line_from_po_line(
            self.purchase_order_line_id)
        self.update(data)
        self._remove_other_data_origin('purchase_order_line_id')

    @api.multi
    def _remove_other_data_origin(self, exception):
        res = super(RmaOrderLine, self)._remove_other_data_origin(exception)
        if not exception == 'purchase_order_line_id':
            self.purchase_order_line_id = False
        return res


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
