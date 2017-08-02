# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

import openerp.addons.decimal_precision as dp
from openerp import _, api, exceptions, fields, models


class RmaLineMakeSupplierRma(models.TransientModel):
    _name = "rma.order.line.make.supplier.rma"
    _description = "RMA Line Make Supplier RMA"

    partner_id = fields.Many2one('res.partner', string='Supplier',
                                 required=False,
                                 domain=[('supplier', '=', True)])
    item_ids = fields.One2many(
        'rma.order.line.make.supplier.rma.item',
        'wiz_id', string='Items')
    supplier_rma_id = fields.Many2one('rma.order',
                                      string='Supplier RMA Order',
                                      required=False,
                                      domain=[('state', '=', 'draft')])

    @api.model
    def _prepare_item(self, line):
        return {
            'line_id': line.id,
            'product_id': line.product_id.id,
            'name': line.name,
            'product_qty': line.qty_to_supplier_rma,
            'uom_id': line.uom_id.id,
        }

    @api.model
    def default_get(self, fields):
        res = super(RmaLineMakeSupplierRma, self).default_get(
            fields)
        rma_line_obj = self.env['rma.order.line']
        rma_line_ids = self.env.context['active_ids'] or []
        active_model = self.env.context['active_model']

        if not rma_line_ids:
            return res
        assert active_model == 'rma.order.line', 'Bad context propagation'

        items = []
        lines = rma_line_obj.browse(rma_line_ids)
        for line in lines:
            items.append([0, 0, self._prepare_item(line)])
        suppliers = lines.mapped('supplier_address_id')
        if len(suppliers) == 1:
            res['partner_id'] = suppliers.id
        else:
            raise exceptions.Warning(
                _('Only RMA lines from the same supplier address can be '
                  'processed at the same time'))
        res['item_ids'] = items
        return res

    @api.model
    def _prepare_supplier_rma(self, company):
        if not self.partner_id:
            raise exceptions.Warning(
                _('Enter a supplier.'))
        return {
            'partner_id': self.partner_id.id,
            'delivery_address_id': self.partner_id.id,
            'type': 'supplier',
            'company_id': company.id,
        }

    @api.model
    def _prepare_supplier_rma_line(self, rma, item):
        operation = self.env['rma.operation'].search(
            [('type', '=', 'supplier')], limit=1)
        return {
            'origin': item.line_id.rma_id.name,
            'delivery_address_id':
                item.line_id.delivery_address_id.id,
            'product_id': item.line_id.product_id.id,
            'customer_rma_id': item.line_id.id,
            'product_qty': item.product_qty,
            'rma_id': rma.id,
            'operation_id': operation.id,
            'receipt_policy': operation.receipt_policy,
            'delivery_policy': operation.delivery_policy,
            'in_warehouse_id': operation.in_warehouse_id.id,
            'out_warehouse_id': operation.out_warehouse_id.id,
            'location_id': operation.location_id.id,
            'supplier_to_customer': operation.supplier_to_customer,
            'in_route_id': operation.in_route_id.id,
            'out_route_id': operation.out_route_id.id,
        }

    @api.multi
    def make_supplier_rma(self):
        res = []
        rma_obj = self.env['rma.order']
        rma_line_obj = self.env['rma.order.line']
        rma = False

        for item in self.item_ids:
            line = item.line_id
            if item.product_qty <= 0.0:
                raise exceptions.Warning(
                    _('Enter a positive quantity.'))

            if self.supplier_rma_id:
                rma = self.supplier_rma_id
            if not rma:
                rma_data = self._prepare_supplier_rma(line.company_id)
                rma = rma_obj.create(rma_data)

            rma_line_data = self._prepare_supplier_rma_line(rma, item)
            rma_line_obj.create(rma_line_data)
            res.append(rma.id)

        return {
            'domain': "[('id','in', ["+','.join(map(str, res))+"])]",
            'name': _('Supplier RMA'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'rma.order',
            'view_id': False,
            'context': {'supplier': 1},
            'type': 'ir.actions.act_window'
        }


class RmaLineMakeRmaOrderItem(models.TransientModel):
    _name = "rma.order.line.make.supplier.rma.item"
    _description = "RMA Line Make Supplier RMA Item"

    wiz_id = fields.Many2one(
        'rma.order.line.make.supplier.rma',
        string='Wizard', required=True, ondelete='cascade',
        readonly=True)
    line_id = fields.Many2one('rma.order.line',
                              string='RMA Line',
                              required=True)
    rma_id = fields.Many2one('rma.order', related='line_id.rma_id',
                             string='RMA Order', readonly=True)
    product_id = fields.Many2one('product.product',
                                 related='line_id.product_id', readony=True)
    name = fields.Char(related='line_id.name', readonly=True)
    uom_id = fields.Many2one('product.uom', string='UoM', readonly=True)
    product_qty = fields.Float(string='Quantity to sell',
                               digits=dp.get_precision('Product UoS'))
