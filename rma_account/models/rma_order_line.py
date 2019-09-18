# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons import decimal_precision as dp


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.model
    def _default_invoice_address(self):
        partner_id = self.env.context.get('partner_id')
        if partner_id:
            return self.env['res.partner'].browse(partner_id)
        return self.env['res.partner']

    @api.multi
    @api.depends('refund_line_ids', 'refund_line_ids.invoice_id.state',
                 'refund_policy', 'type')
    def _compute_qty_refunded(self):
        for rec in self:
            rec.qty_refunded = sum(rec.refund_line_ids.filtered(
                lambda i: i.invoice_id.state in ('open', 'paid')).mapped(
                'quantity'))

    @api.depends('refund_line_ids', 'refund_line_ids.invoice_id.state',
                 'refund_policy', 'move_ids', 'move_ids.state', 'type')
    def _compute_qty_to_refund(self):
        qty = 0.0
        for res in self:
            if res.refund_policy == 'ordered':
                qty = res.product_qty - res.qty_refunded
            elif res.refund_policy == 'received':
                qty = res.qty_received - res.qty_refunded
            elif res.refund_policy == 'delivered':
                qty = res.qty_delivered - res.qty_refunded
            res.qty_to_refund = qty

    @api.multi
    def _compute_refund_count(self):
        for rec in self:
            rec.refund_count = len(rec.refund_line_ids.mapped('invoice_id'))

    invoice_address_id = fields.Many2one(
        'res.partner', string='Partner invoice address',
        default=lambda self: self._default_invoice_address(),
        readonly=True, states={'draft': [('readonly', False)]},
        help="Invoice address for current rma order.",
    )
    refund_count = fields.Integer(
        compute='_compute_refund_count', string='# of Refunds', default=0)
    invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string='Originating Invoice Line',
        ondelete='restrict',
        index=True,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    refund_line_ids = fields.One2many(
        comodel_name='account.invoice.line',
        inverse_name='rma_line_id', string='Refund Lines',
        copy=False, index=True, readonly=True,
    )
    invoice_id = fields.Many2one('account.invoice', string='Source',
                                 related='invoice_line_id.invoice_id',
                                 index=True, readonly=True)
    refund_policy = fields.Selection([
        ('no', 'No refund'), ('ordered', 'Based on Ordered Quantities'),
        ('delivered', 'Based on Delivered Quantities'),
        ('received', 'Based on Received Quantities')], string="Refund Policy",
        required=True, default='no',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    qty_to_refund = fields.Float(
        string='Qty To Refund', copy=False,
        digits=dp.get_precision('Product Unit of Measure'), readonly=True,
        compute='_compute_qty_to_refund', store=True)
    qty_refunded = fields.Float(
        string='Qty Refunded', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute='_compute_qty_refunded', store=True)

    @api.onchange('product_id', 'partner_id')
    def _onchange_product_id(self):
        """Domain for sale_line_id is computed here to make it dynamic."""
        res = super(RmaOrderLine, self)._onchange_product_id()
        if not res.get('domain'):
            res['domain'] = {}
        domain = [
            '|',
            ('invoice_id.partner_id', '=', self.partner_id.id),
            ('invoice_id.partner_id', 'child_of', self.partner_id.id)]
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
        res['domain']['invoice_line_id'] = domain
        return res

    @api.multi
    def _prepare_rma_line_from_inv_line(self, line):
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
                raise ValidationError(_("Please define an rma route"))

        if not operation.in_warehouse_id or not operation.out_warehouse_id:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id),
                 ('lot_rma_id', '!=', False)], limit=1)
            if not warehouse:
                raise ValidationError(_("Please define a warehouse with a"
                                      " default rma location"))
        data = {
            'product_id': line.product_id.id,
            'origin': line.invoice_id.number,
            'uom_id': line.uom_id.id,
            'operation_id': operation.id,
            'product_qty': line.quantity,
            'price_unit': line.invoice_id.currency_id.compute(
                line.price_unit, line.currency_id, round=False),
            'delivery_address_id': line.invoice_id.partner_id.id,
            'invoice_address_id': line.invoice_id.partner_id.id,
            'receipt_policy': operation.receipt_policy,
            'refund_policy': operation.refund_policy,
            'delivery_policy': operation.delivery_policy,
            'currency_id': line.currency_id.id,
            'in_warehouse_id': operation.in_warehouse_id.id or warehouse.id,
            'out_warehouse_id': operation.out_warehouse_id.id or warehouse.id,
            'in_route_id': operation.in_route_id.id or route.id,
            'out_route_id': operation.out_route_id.id or route.id,
            'location_id': (operation.location_id.id or
                            operation.in_warehouse_id.lot_rma_id.id or
                            warehouse.lot_rma_id.id),
        }
        return data

    @api.onchange('invoice_line_id')
    def _onchange_invoice_line_id(self):
        if not self.invoice_line_id:
            return
        data = self._prepare_rma_line_from_inv_line(
            self.invoice_line_id)
        self.update(data)
        self._remove_other_data_origin('invoice_line_id')

    @api.multi
    @api.constrains('invoice_line_id', 'partner_id')
    def _check_invoice_partner(self):
        for rec in self:
            if (rec.invoice_line_id and
                    rec.invoice_line_id.invoice_id.partner_id !=
                    rec.partner_id):
                raise ValidationError(_(
                    "RMA customer and originating invoice line customer "
                    "doesn't match."))

    @api.multi
    def _remove_other_data_origin(self, exception):
        res = super(RmaOrderLine, self)._remove_other_data_origin(exception)
        if not exception == 'invoice_line_id':
            self.invoice_line_id = False
        return res

    @api.onchange('operation_id')
    def _onchange_operation_id(self):
        result = super(RmaOrderLine, self)._onchange_operation_id()
        if self.operation_id:
            self.refund_policy = self.operation_id.refund_policy or 'no'
        return result

    @api.multi
    @api.constrains('invoice_line_id')
    def _check_duplicated_lines(self):
        for line in self:
            matching_inv_lines = self.env['account.invoice.line'].search([(
                'id', '=', line.invoice_line_id.id)])
            if len(matching_inv_lines) > 1:
                    raise UserError(
                        _("There's an rma for the invoice line %s "
                          "and invoice %s" %
                          (line.invoice_line_id,
                           line.invoice_line_id.invoice_id)))
        return {}

    @api.multi
    def action_view_invoice(self):
        action = self.env.ref('account.action_invoice_tree')
        result = action.read()[0]
        res = self.env.ref('account.invoice_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['view_id'] = res and res.id or False
        result['res_id'] = self.invoice_line_id.invoice_id.id
        return result

    @api.multi
    def action_view_refunds(self):
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        invoice_ids = self.mapped('refund_line_ids.invoice_id').ids
        if invoice_ids:
            # choose the view_mode accordingly
            if len(invoice_ids) > 1:
                result['domain'] = [('id', 'in', invoice_ids)]
            else:
                res = self.env.ref('account.invoice_supplier_form', False)
                result['views'] = [(res and res.id or False, 'form')]
                result['res_id'] = invoice_ids[0]
        return result

    @api.multi
    def name_get(self):
        res = []
        if self.env.context.get('rma'):
            for rma in self:
                res.append((rma.id, "%s %s qty:%s" % (
                    rma.name,
                    rma.product_id.name,
                    rma.product_qty)))
            return res
        else:
            return super(RmaOrderLine, self).name_get()
