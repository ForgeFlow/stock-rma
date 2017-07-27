# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

import time
from openerp import models, fields, exceptions, api, _
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT_FORMAT
import openerp.addons.decimal_precision as dp


class RmaAddPurchase(models.TransientModel):
    _name = 'rma_add_purchase'
    _description = 'Wizard to add rma lines'

    @api.model
    def default_get(self, fields):
        res = super(RmaAddPurchase, self).default_get(fields)
        rma_obj = self.env['rma.order']
        rma_id = self.env.context['active_ids'] or []
        active_model = self.env.context['active_model']
        if not rma_id:
            return res
        assert active_model == 'rma.order', 'Bad context propagation'

        rma = rma_obj.browse(rma_id)
        res['rma_id'] = rma.id
        res['partner_id'] = rma.partner_id.id
        res['purchase_id'] = False
        res['purchase_line_ids'] = False
        return res

    rma_id = fields.Many2one('rma.order',
                              string='RMA Order',
                              readonly=True,
                              ondelete='cascade')

    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner',
                                 readonly=True)
    purchase_id = fields.Many2one(comodel_name='purchase.order', string='Order')
    purchase_line_ids = fields.Many2many('purchase.order.line',
                                     'rma_add_purchase_add_line_rel',
                                     'purchase_line_id', 'rma_add_purchase_id',
                                     readonly=False,
                                     string='Purcahse Order Lines')

    def _prepare_rma_line_from_po_line(self, line):
        operation = line.product_id.rma_operation_id and \
                    line.product_id.rma_operation_id.id or False
        if not operation:
            operation = line.product_id.categ_id.rma_operation_id and \
                        line.product_id.categ_id.rma_operation_id.id or False
        data = {
            'purchase_order_line_id': line.id,
            'product_id': line.product_id.id,
            'origin': line.order_id.name,
            'uom_id': line.product_uom.id,
            'operation_id': operation,
            'product_qty': line.product_qty,
            'price_unit': line.currency_id.compute(
                line.price_unit, line.currency_id, round=False),
            'rma_id': self.rma_id.id
        }
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
        data.update(
            {'in_route_id': operation.in_route_id.id or route,
             'out_route_id': operation.out_route_id.id or route,
             'receipt_policy': operation.receipt_policy,
             'location_id': operation.location_id.id or
                            self.env.ref('stock.stock_location_stock').id,
             'operation_id': operation.id,
             'refund_policy': operation.refund_policy,
             'delivery_policy': operation.delivery_policy
             })
        return data

    @api.model
    def _get_rma_data(self):
        data = {
            'date_rma': fields.Datetime.now(),
            'delivery_address_id': self.purchase_id.partner_id.id,
            'invoice_address_id': self.purchase_id.partner_id.id
        }
        return data

    @api.model
    def _get_existing_purchase_lines(self):
        existing_purchase_lines = []
        for rma_line in self.rma_id.rma_line_ids:
            existing_purchase_lines.append(rma_line.purchase_order_line_id)
        return existing_purchase_lines

    @api.multi
    def add_lines(self):
        rma_line_obj = self.env['rma.order.line']
        existing_purchase_lines = self._get_existing_purchase_lines()
        for line in self.purchase_line_ids:
            # Load a PO line only once
            if line not in existing_purchase_lines:
                data = self._prepare_rma_line_from_po_line(line)
                rma_line_obj.create(data)
        rma = self.rma_id
        data_rma = self._get_rma_data()
        rma.write(data_rma)
        return {'type': 'ir.actions.act_window_close'}
