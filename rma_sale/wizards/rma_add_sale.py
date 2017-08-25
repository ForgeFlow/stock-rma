# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class RmaAddSale(models.TransientModel):
    _name = 'rma_add_sale'
    _description = 'Wizard to add rma lines from SO lines'

    @api.model
    def default_get(self, fields):
        res = super(RmaAddSale, self).default_get(fields)
        rma_obj = self.env['rma.order']
        rma_id = self.env.context['active_ids'] or []
        active_model = self.env.context['active_model']
        if not rma_id:
            return res
        assert active_model == 'rma.order', 'Bad context propagation'

        rma = rma_obj.browse(rma_id)
        res['rma_id'] = rma.id
        res['partner_id'] = rma.partner_id.id
        res['sale_id'] = False
        res['sale_line_ids'] = False
        return res

    rma_id = fields.Many2one(
        comodel_name='rma.order', string='RMA Order', readonly=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner',
                                 readonly=True)
    sale_id = fields.Many2one(comodel_name='sale.order', string='Order')
    sale_line_ids = fields.Many2many('sale.order.line',
                                     'rma_add_sale_add_line_rel',
                                     'sale_line_id', 'rma_add_sale_id',
                                     readonly=False,
                                     string='Sale Lines')

    def _prepare_rma_line_from_sale_order_line(self, line):
        operation = line.product_id.rma_customer_operation_id
        if not operation:
            operation = line.product_id.categ_id.rma_customer_operation_id
        if not operation:
            operation = self.env['rma.operation'].search(
                [('type', '=', self.rma_id.type)], limit=1)
            if not operation:
                raise ValidationError("Please define an operation first")
        if not operation.in_route_id or not operation.out_route_id:
            route = self.env['stock.location.route'].search(
                [('rma_selectable', '=', True)], limit=1)
            if not route:
                raise ValidationError("Please define an rma route")
        if not operation.in_warehouse_id or not operation.out_warehouse_id:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.rma_id.company_id.id),
                 ('lot_rma_id', '!=', False)], limit=1)
            if not warehouse:
                raise ValidationError("Please define a warehouse with a "
                                      "default rma location.")
        data = {
            'sale_line_id': line.id,
            'product_id': line.product_id.id,
            'origin': line.order_id.name,
            'uom_id': line.product_uom.id,
            'operation_id': operation.id,
            'product_qty': line.product_uom_qty,
            'delivery_address_id': self.sale_id.partner_id.id,
            'invoice_address_id': self.sale_id.partner_id.id,
            'price_unit': line.currency_id.compute(
                line.price_unit, line.currency_id, round=False),
            'rma_id': self.rma_id.id,
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

    @api.model
    def _get_rma_data(self):
        data = {
            'date_rma': fields.Datetime.now(),
            'delivery_address_id': self.sale_id.partner_id.id,
            'invoice_address_id': self.sale_id.partner_id.id
        }
        return data

    @api.model
    def _get_existing_sale_lines(self):
        existing_sale_lines = []
        for rma_line in self.rma_id.rma_line_ids:
            existing_sale_lines.append(rma_line.sale_line_id)
        return existing_sale_lines

    @api.multi
    def add_lines(self):
        rma_line_obj = self.env['rma.order.line']
        existing_sale_lines = self._get_existing_sale_lines()
        for line in self.sale_line_ids:
            # Load a PO line only once
            if line not in existing_sale_lines:
                data = self._prepare_rma_line_from_sale_order_line(line)
                rma_line_obj.create(data)
        rma = self.rma_id
        data_rma = self._get_rma_data()
        rma.write(data_rma)
        return {'type': 'ir.actions.act_window_close'}
