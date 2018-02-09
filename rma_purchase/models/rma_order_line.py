# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.multi
    def _compute_purchase_count(self):
        for rec in self:
            rec.purchase_count = len(self.env['purchase.order'].search(
                [('origin', 'ilike', rec.name)]).ids)

    @api.multi
    def _compute_purchase_order_lines(self):
        for rec in self:
            purchase_list = []
            for purchase in self.env['purchase.order'].search(
                    [('origin', 'ilike', rec.name)]):
                for line in purchase.order_line:
                    purchase_list.append(line.id)
            rec.purchase_order_line_ids = [(6, 0, purchase_list)]

    purchase_count = fields.Integer(
        compute='_compute_purchase_count', string='# of Purchases',
    )
    purchase_order_line_id = fields.Many2one(
        comodel_name='purchase.order.line', string='Originating Purchase Line',
        ondelete='restrict',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    purchase_id = fields.Many2one(
        string="Source Purchase Order",
        related='purchase_order_line_id.order_id',
        readonly=True,
    )
    purchase_order_line_ids = fields.Many2many(
        comodel_name='purchase.order.line',
        relation='purchase_line_rma_line_rel',
        column1='rma_order_line_id', column2='purchase_order_line_id',
        string='Purchase Order Lines', compute='_compute_purchase_order_lines',
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
    @api.constrains('purchase_order_line_id', 'partner_id')
    def _check_purchase_partner(self):
        for rec in self:
            if (rec.purchase_order_line_id and
                    rec.purchase_order_line_id.order_id.partner_id !=
                    rec.partner_id):
                raise ValidationError(_(
                    "RMA customer and originating purchase line customer "
                    "doesn't match."))

    @api.multi
    def _remove_other_data_origin(self, exception):
        res = super(RmaOrderLine, self)._remove_other_data_origin(exception)
        if not exception == 'purchase_order_line_id':
            self.purchase_order_line_id = False
        return res
