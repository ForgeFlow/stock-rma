# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class RmaOperation(models.Model):
    _name = 'rma.operation'
    _description = 'RMA Operation'

    @api.model
    def _default_warehouse_id(self):
        company_id = self.env.user.company_id.id
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', company_id)], limit=1)
        return warehouse

    @api.model
    def _default_customer_location_id(self):
        return self.env.ref('stock.stock_location_customers') or False

    @api.model
    def _default_supplier_location_id(self):
        return self.env.ref('stock.stock_location_suppliers') or False

    name = fields.Char('Description', required=True)
    code = fields.Char('Code', required=True)
    active = fields.Boolean(string='Active', default=True)
    receipt_policy = fields.Selection([
        ('no', 'Not required'), ('ordered', 'Based on Ordered Quantities'),
        ('delivered', 'Based on Delivered Quantities')],
        string="Receipts Policy", default='no')
    delivery_policy = fields.Selection([
        ('no', 'Not required'), ('ordered', 'Based on Ordered Quantities'),
        ('received', 'Based on Received Quantities')],
        string="Delivery Policy", default='no')
    in_route_id = fields.Many2one(
        'stock.location.route', string='Inbound Route',
        domain=[('rma_selectable', '=', True)])
    out_route_id = fields.Many2one(
        'stock.location.route', string='Outbound Route',
        domain=[('rma_selectable', '=', True)])
    customer_to_supplier = fields.Boolean(
        'The customer will send to the supplier', default=False)
    supplier_to_customer = fields.Boolean(
        'The supplier will send to the customer', default=False)
    in_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse', string='Inbound Warehouse',
        default=_default_warehouse_id)
    out_warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse', string='Outbound Warehouse',
        default=_default_warehouse_id)
    location_id = fields.Many2one(
        'stock.location', 'Send To This Company Location')
    type = fields.Selection([
        ('customer', 'Customer'), ('supplier', 'Supplier')],
        string="Used in RMA of this type", required=True)
    rma_line_ids = fields.One2many('rma.order.line', 'operation_id',
                                   'RMA lines')
