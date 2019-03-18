# Copyright (C) 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.addons import decimal_precision as dp
import operator
ops = {'=': operator.eq,
       '!=': operator.ne}


class RmaOrderLine(models.Model):
    _name = "rma.order.line"
    _inherit = ['mail.thread']

    @api.model
    def _get_default_type(self):
        if 'supplier' in self.env.context:
            return "supplier"
        return "customer"

    @api.model
    def _default_warehouse_id(self):
        rma_id = self.env.context.get('default_rma_id', False)
        warehouse = self.env['stock.warehouse']
        if rma_id:
            rma = self.env['rma.order'].browse(rma_id)
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', rma.company_id.id)], limit=1)
        return warehouse

    @api.model
    def _default_location_id(self):
        wh = self._default_warehouse_id()
        return wh.lot_rma_id

    @api.model
    def _default_delivery_address(self):
        partner_id = self.env.context.get('partner_id', False)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            addr = partner.address_get(['delivery'])
            return self.env['res.partner'].browse(addr['delivery'])
        return False

    @api.multi
    def _compute_in_shipment_count(self):
        for line in self:
            picking_ids = []
            for move in line.move_ids:
                if move.location_dest_id.usage == 'internal':
                    picking_ids.append(move.picking_id.id)
                else:
                    if line.customer_to_supplier:
                        picking_ids.append(move.picking_id.id)
            shipments = list(set(picking_ids))
            line.in_shipment_count = len(shipments)

    @api.multi
    def _compute_out_shipment_count(self):
        picking_ids = []
        for line in self:
            for move in line.move_ids:
                if move.location_dest_id.usage in ('supplier', 'customer'):
                    if not line.customer_to_supplier:
                        picking_ids.append(move.picking_id.id)
            shipments = list(set(picking_ids))
            line.out_shipment_count = len(shipments)

    @api.multi
    def _get_rma_move_qty(self, states, direction='in'):
        for rec in self:
            product_obj = self.env['uom.uom']
            qty = 0.0
            if direction == 'in':
                op = ops['=']
            else:
                op = ops['!=']
            for move in rec.move_ids.filtered(
                    lambda m: m.state in states and op(m.location_id.usage,
                                                       rec.type)):
                qty += product_obj._compute_quantity(
                    move.product_uom_qty, rec.uom_id)
            return qty

    @api.multi
    @api.depends('move_ids', 'move_ids.state', 'qty_received',
                 'receipt_policy', 'product_qty', 'type')
    def _compute_qty_to_receive(self):
        for rec in self:
            rec.qty_to_receive = 0.0
            if rec.receipt_policy == 'ordered':
                rec.qty_to_receive = \
                    rec.product_qty - rec.qty_received
            elif rec.receipt_policy == 'delivered':
                rec.qty_to_receive = \
                    rec.qty_delivered - rec.qty_received

    @api.multi
    @api.depends('move_ids', 'move_ids.state',
                 'delivery_policy', 'product_qty', 'type', 'qty_delivered',
                 'qty_received')
    def _compute_qty_to_deliver(self):
        for rec in self:
            rec.qty_to_deliver = 0.0
            if rec.delivery_policy == 'ordered':
                rec.qty_to_deliver = rec.product_qty - rec.qty_delivered
            elif rec.delivery_policy == 'received':
                rec.qty_to_deliver = rec.qty_received - rec.qty_delivered

    @api.multi
    @api.depends('move_ids', 'move_ids.state', 'type')
    def _compute_qty_incoming(self):
        for rec in self:
            qty = rec._get_rma_move_qty(
                ('draft', 'confirmed', 'assigned'), direction='in')
            rec.qty_incoming = qty

    @api.multi
    @api.depends('move_ids', 'move_ids.state', 'type')
    def _compute_qty_received(self):
        for rec in self:
            qty = rec._get_rma_move_qty('done', direction='in')
            rec.qty_received = qty

    @api.multi
    @api.depends('move_ids', 'move_ids.state', 'type')
    def _compute_qty_outgoing(self):
        for rec in self:
            qty = rec._get_rma_move_qty(
                ('draft', 'confirmed', 'assigned'), direction='out')
            rec.qty_outgoing = qty

    @api.multi
    @api.depends('move_ids', 'move_ids.state', 'type')
    def _compute_qty_delivered(self):
        for rec in self:
            qty = rec._get_rma_move_qty('done', direction='out')
            rec.qty_delivered = qty

    @api.model
    def _get_supplier_rma_qty(self):
        return sum(self.supplier_rma_line_ids.filtered(
            lambda r: r.state != 'cancel').mapped(
            'product_qty'))

    @api.multi
    @api.depends('customer_to_supplier', 'supplier_rma_line_ids',
                 'move_ids', 'move_ids.state', 'qty_received',
                 'receipt_policy', 'product_qty', 'type')
    def _compute_qty_supplier_rma(self):
        for rec in self:
            if rec.customer_to_supplier:
                supplier_rma_qty = rec._get_supplier_rma_qty()
                rec.qty_to_supplier_rma = rec.product_qty - supplier_rma_qty
                rec.qty_in_supplier_rma = supplier_rma_qty
            else:
                rec.qty_to_supplier_rma = 0.0
                rec.qty_in_supplier_rma = 0.0

    @api.multi
    def _compute_rma_line_count(self):
        for rec in self.filtered(lambda r: r.type == 'customer'):
            rec.rma_line_count = len(rec.supplier_rma_line_ids)
        for rec in self.filtered(lambda r: r.type == 'supplier'):
            rec.rma_line_count = len(rec.customer_rma_id)

    delivery_address_id = fields.Many2one(
        comodel_name='res.partner', string='Partner delivery address',
        default=lambda self: self._default_delivery_address(),
        readonly=True, states={'draft': [('readonly', False)]},
        help="This address will be used to deliver repaired or replacement "
             "products.",
    )
    rma_id = fields.Many2one(
        comodel_name='rma.order', string='RMA Group',
        track_visibility='onchange', readonly=True,
    )
    name = fields.Char(
        string='Reference', required=True, default='/',
        readonly=True, states={'draft': [('readonly', False)]},
        help='Add here the supplier RMA #. Otherwise an internal code is'
             ' assigned.',
    )
    description = fields.Text(string='Description')
    origin = fields.Char(
        string='Source Document',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Reference of the document that produced this rma.")
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('to_approve', 'To Approve'),
                   ('approved', 'Approved'),
                   ('done', 'Done')],
        string='State', default='draft',
        track_visibility='onchange',
    )
    operation_id = fields.Many2one(
        comodel_name="rma.operation", string="Operation",
        readonly=True, states={'draft': [('readonly', False)]},
    )
    assigned_to = fields.Many2one(
        comodel_name='res.users', track_visibility='onchange',
        default=lambda self: self.env.uid,
    )
    requested_by = fields.Many2one(
        comodel_name='res.users', track_visibility='onchange',
        default=lambda self: self.env.uid,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner', required=True, store=True,
        track_visibility='onchange',
        string="Partner",
        readonly=True, states={'draft': [('readonly', False)]},
    )
    sequence = fields.Integer(
        default=10,
        help="Gives the sequence of this line when displaying the rma.")
    product_id = fields.Many2one(
        comodel_name='product.product', string='Product',
        ondelete='restrict', required=True,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    product_tracking = fields.Selection(related="product_id.tracking")
    lot_id = fields.Many2one(
        comodel_name="stock.production.lot", string="Lot/Serial Number",
        readonly=True, states={"draft": [("readonly", False)]},
    )
    product_qty = fields.Float(
        string='Ordered Qty', copy=False, default=1.0,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, states={'draft': [('readonly', False)]},
    )
    uom_id = fields.Many2one(
        comodel_name='uom.uom', string='Unit of Measure',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    price_unit = fields.Monetary(
        string='Price Unit',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    in_shipment_count = fields.Integer(compute=_compute_in_shipment_count,
                                       string='# of Shipments')
    out_shipment_count = fields.Integer(compute=_compute_out_shipment_count,
                                        string='# of Deliveries')
    move_ids = fields.One2many('stock.move', 'rma_line_id',
                               string='Stock Moves', readonly=True,
                               copy=False)
    reference_move_id = fields.Many2one(
        comodel_name='stock.move', string='Originating Stock Move',
        copy=False,
        readonly=True, states={'draft': [('readonly', False)]},
    )
    currency_id = fields.Many2one('res.currency', string="Currency")
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        default=lambda self: self.env.user.company_id)
    type = fields.Selection(
        selection=[('customer', 'Customer'), ('supplier', 'Supplier')],
        string="Type", required=True,
        default=lambda self: self._get_default_type(),
        readonly=True,
    )
    customer_to_supplier = fields.Boolean(
        'The customer will send to the supplier',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    supplier_to_customer = fields.Boolean(
        'The supplier will send to the customer',
        readonly=True, states={'draft': [('readonly', False)]},
    )
    receipt_policy = fields.Selection([
        ('no', 'Not required'), ('ordered', 'Based on Ordered Quantities'),
        ('delivered', 'Based on Delivered Quantities')],
        required=True, string="Receipts Policy",
        readonly=True, states={'draft': [('readonly', False)]},
    )
    delivery_policy = fields.Selection([
        ('no', 'Not required'), ('ordered', 'Based on Ordered Quantities'),
        ('received', 'Based on Received Quantities')], required=True,
        string="Delivery Policy",
        readonly=True, states={'draft': [('readonly', False)]},
    )
    in_route_id = fields.Many2one(
        'stock.location.route', string='Inbound Route',
        required=True,
        domain=[('rma_selectable', '=', True)],
        readonly=True, states={'draft': [('readonly', False)]},
    )
    out_route_id = fields.Many2one(
        'stock.location.route', string='Outbound Route',
        required=True,
        domain=[('rma_selectable', '=', True)],
        readonly=True, states={'draft': [('readonly', False)]},
    )
    in_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Inbound Warehouse',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self._default_warehouse_id(),
    )
    out_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse', string='Outbound Warehouse',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self._default_warehouse_id(),
    )
    location_id = fields.Many2one(
        comodel_name='stock.location', string='Send To This Company Location',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self._default_location_id(),
    )
    customer_rma_id = fields.Many2one(
        'rma.order.line', string='Customer RMA line', ondelete='cascade')
    supplier_rma_line_ids = fields.One2many(
        'rma.order.line', 'customer_rma_id')
    rma_line_count = fields.Integer(
        compute='_compute_rma_line_count',
        string='# of RMA lines associated',
    )
    supplier_address_id = fields.Many2one(
        comodel_name='res.partner', readonly=True,
        states={'draft': [('readonly', False)]},
        string='Supplier Address',
        help="Address of the supplier in case of Customer RMA operation "
             "dropship.")
    customer_address_id = fields.Many2one(
        comodel_name='res.partner', readonly=True,
        states={'draft': [('readonly', False)]},
        string='Customer Address',
        help="Address of the customer in case of Supplier RMA operation "
             "dropship.")
    qty_to_receive = fields.Float(
        string='Qty To Receive',
        digits=dp.get_precision('Product Unit of Measure'),
        compute=_compute_qty_to_receive, store=True)
    qty_incoming = fields.Float(
        string='Incoming Qty', copy=False,
        readonly=True, digits=dp.get_precision('Product Unit of Measure'),
        compute=_compute_qty_incoming, store=True)
    qty_received = fields.Float(
        string='Qty Received', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        compute=_compute_qty_received,
        store=True)
    qty_to_deliver = fields.Float(
        string='Qty To Deliver', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_to_deliver,
        store=True)
    qty_outgoing = fields.Float(
        string='Outgoing Qty', copy=False,
        readonly=True, digits=dp.get_precision('Product Unit of Measure'),
        compute=_compute_qty_outgoing,
        store=True)
    qty_delivered = fields.Float(
        string='Qty Delivered', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_delivered,
        store=True)
    qty_to_supplier_rma = fields.Float(
        string='Qty to send to Supplier RMA',
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_supplier_rma,
        store=True)
    qty_in_supplier_rma = fields.Float(
        string='Qty in Supplier RMA',
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_supplier_rma,
        store=True)
    under_warranty = fields.Boolean(
        string="Under Warranty?",
        readonly=True, states={'draft': [('readonly', False)]},
    )

    @api.multi
    def _prepare_rma_line_from_stock_move(self, sm, lot=False):
        if not self.type:
            self.type = self._get_default_type()
        if self.type == 'customer':
            operation = sm.product_id.rma_customer_operation_id or \
                sm.product_id.categ_id.rma_customer_operation_id
        else:
            operation = sm.product_id.rma_supplier_operation_id or \
                sm.product_id.categ_id.rma_supplier_operation_id

        if not operation:
            operation = self.env['rma.operation'].search(
                [('type', '=', self.type)], limit=1)
            if not operation:
                raise ValidationError(_("Please define an operation first."))

        if not operation.in_route_id or not operation.out_route_id:
            route = self.env['stock.location.route'].search(
                [('rma_selectable', '=', True)], limit=1)
            if not route:
                raise ValidationError(_("Please define an RMA route."))

        if not operation.in_warehouse_id or not operation.out_warehouse_id:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id),
                 ('lot_rma_id', '!=', False)], limit=1)
            if not warehouse:
                raise ValidationError(
                    _("Please define a warehouse with a default RMA "
                      "location."))

        data = {
            'product_id': sm.product_id.id,
            'lot_id': lot and lot.id or False,
            'origin': sm.picking_id.name or sm.name,
            'uom_id': sm.product_uom.id,
            'product_qty': sm.product_uom_qty,
            'delivery_address_id': sm.picking_id.partner_id.id,
            'operation_id': operation.id,
            'receipt_policy': operation.receipt_policy,
            'delivery_policy': operation.delivery_policy,
            'in_warehouse_id': operation.in_warehouse_id.id or warehouse.id,
            'out_warehouse_id': operation.out_warehouse_id.id or warehouse.id,
            'in_route_id': operation.in_route_id.id or route.id,
            'out_route_id': operation.out_route_id.id or route.id,
            'location_id': (operation.location_id.id or
                            operation.in_warehouse_id.lot_rma_id.id or
                            warehouse.lot_rma_id.id)
        }
        return data

    @api.multi
    @api.onchange('reference_move_id')
    def _onchange_reference_move_id(self):
        self.ensure_one()
        sm = self.reference_move_id
        if not sm:
            return
        if sm.move_line_ids.lot_id:
            if len(sm.move_line_ids.lot_id) > 1:
                raise UserError(_('To manage lots use RMA groups.'))
            else:
                data = self._prepare_rma_line_from_stock_move(
                    sm, lot=sm.move_line_ids.lot_id[0])
                self.update(data)
        else:
            data = self._prepare_rma_line_from_stock_move(
                sm, lot=False)
            self.update(data)
        self._remove_other_data_origin('reference_move_id')

    @api.multi
    @api.constrains('reference_move_id', 'partner_id')
    def _check_move_partner(self):
        for rec in self:
            if (rec.reference_move_id and
                    rec.reference_move_id.picking_id.partner_id !=
                    rec.partner_id):
                raise ValidationError(_(
                    "RMA customer and originating stock move customer "
                    "doesn't match."))

    @api.multi
    def _remove_other_data_origin(self, exception):
        if not exception == 'reference_move_id':
            self.reference_move_id = False
        return True

    @api.multi
    def action_rma_to_approve(self):
        self.write({'state': 'to_approve'})
        for rec in self:
            if rec.product_id.rma_approval_policy == 'one_step':
                rec.action_rma_approve()
        return True

    @api.multi
    def action_rma_draft(self):
        if self.in_shipment_count or self.out_shipment_count:
            raise UserError(_(
                "You cannot reset to draft a RMA with related pickings."))
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_rma_approve(self):
        self.write({'state': 'approved'})
        return True

    @api.multi
    def action_rma_done(self):
        self.write({'state': 'done'})
        return True

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('name') == '/':
            if self.env.context.get('supplier'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'rma.order.line.supplier')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'rma.order.line.customer')
        return super(RmaOrderLine, self).create(vals)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result
        self.uom_id = self.product_id.uom_id.id
        self.price_unit = self.product_id.standard_price
        if not self.type:
            self.type = self._get_default_type()
        if self.type == 'customer':
            self.operation_id = self.product_id.rma_customer_operation_id or \
                self.product_id.categ_id.rma_customer_operation_id
        else:
            self.operation_id = self.product_id.rma_supplier_operation_id or \
                self.product_id.categ_id.rma_supplier_operation_id
        if self.lot_id.product_id != self.product_id:
            self.lot_id = False
        return {'domain': {
            'lot_id': [('product_id', '=', self.product_id.id)]}}

    @api.onchange('operation_id')
    def _onchange_operation_id(self):
        result = {}
        if not self.operation_id:
            return result
        self.receipt_policy = self.operation_id.receipt_policy
        self.delivery_policy = self.operation_id.delivery_policy
        self.in_warehouse_id = self.operation_id.in_warehouse_id
        self.out_warehouse_id = self.operation_id.out_warehouse_id
        self.location_id = self.operation_id.location_id or \
            self.in_warehouse_id.lot_rma_id
        self.customer_to_supplier = self.operation_id.customer_to_supplier
        self.supplier_to_customer = self.operation_id.supplier_to_customer
        self.in_route_id = self.operation_id.in_route_id
        self.out_route_id = self.operation_id.out_route_id
        return result

    @api.onchange('customer_to_supplier', 'type')
    def _onchange_receipt_policy(self):
        if self.type == 'supplier' and self.customer_to_supplier:
            self.receipt_policy = 'no'
        elif self.type == 'customer' and self.supplier_to_customer:
            self.delivery_policy = 'no'

    @api.onchange("lot_id")
    def _onchange_lot_id(self):
        product = self.lot_id.product_id
        if product:
            self.product_id = product
            self.uom_id = product.uom_id

    @api.multi
    def action_view_in_shipments(self):
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        picking_ids = []
        for line in self:
            for move in line.move_ids:
                if move.location_dest_id.usage == 'internal':
                    picking_ids.append(move.picking_id.id)
                else:
                    if line.customer_to_supplier:
                        picking_ids.append(move.picking_id.id)

        shipments = list(set(picking_ids))
        # choose the view_mode accordingly
        if len(shipments) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(shipments) + ")]"
        elif len(shipments) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = shipments[0]
        return result

    @api.multi
    def action_view_out_shipments(self):
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        picking_ids = []
        for line in self:
            for move in line.move_ids:
                if move.location_dest_id.usage in ('supplier', 'customer'):
                    if not line.customer_to_supplier:
                        picking_ids.append(move.picking_id.id)
        shipments = list(set(picking_ids))
        # choose the view_mode accordingly
        if len(shipments) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(shipments) + ")]"
        elif len(shipments) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = shipments[0]
        return result

    @api.multi
    def action_view_rma_lines(self):
        if self.type == 'customer':
            # from customer we link to supplier rma
            action = self.env.ref(
                'rma.action_rma_supplier_lines')
            rma_lines = self.supplier_rma_line_ids.ids
            res = self.env.ref('rma.view_rma_line_supplier_form', False)
        else:
            # from supplier we link to customer rma
            action = self.env.ref(
                'rma.action_rma_customer_lines')
            rma_lines = self.customer_rma_id.ids
            res = self.env.ref('rma.view_rma_line_form', False)
        result = action.read()[0]
        # choose the view_mode accordingly
        if rma_lines and len(rma_lines) != 1:
            result['domain'] = rma_lines.ids
        elif len(rma_lines) == 1:
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = rma_lines[0]
        return result
