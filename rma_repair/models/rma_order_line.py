# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import api, fields, models
from openerp.addons import decimal_precision as dp


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.one
    @api.depends('repair_ids', 'repair_type', 'repair_ids.state',
                 'qty_to_receive')
    def _compute_qty_to_repair(self):
        if self.repair_type == 'no':
            self.qty_to_repair = 0.0
        elif self.repair_type == 'ordered':
            qty = self._get_rma_repaired_qty()
            self.qty_to_repair = self.product_qty - qty
        elif self.repair_type == 'received':
            qty = self._get_rma_repaired_qty()
            self.qty_to_repair = self.qty_received - qty
        else:
            self.qty_to_repair = 0.0

    @api.one
    @api.depends('repair_ids', 'repair_type', 'repair_ids.state',
                 'qty_to_receive')
    def _compute_qty_repaired(self):
        self.qty_repaired = self._get_rma_repaired_qty()

    @api.multi
    def _compute_repair_count(self):
        for line in self:
            line.repair_count = len(line.repair_ids)

    repair_ids = fields.One2many(
        comodel_name='mrp.repair', inverse_name='rma_line_id',
        string='Repair Orders', readonly=True,
        states={'draft': [('readonly', False)]}, copy=False)
    qty_to_repair = fields.Float(
        string='Qty To Repair', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_to_repair,
        store=True)
    qty_repaired = fields.Float(
        string='Qty Repaired', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_repaired,
        store=True, help="Quantity repaired or being repaired.")
    repair_type = fields.Selection(selection=[
        ('no', 'Not required'), ('ordered', 'Based on Ordered Quantities'),
        ('received', 'Based on Received Quantities')],
        string="Repair Policy", default='no', required=True)
    repair_count = fields.Integer(
        compute=_compute_repair_count, string='# of Repairs')

    @api.multi
    def action_view_repair_order(self):
        action = self.env.ref('mrp_repair.action_repair_order_tree')
        result = action.read()[0]
        repair_ids = self.repair_ids.ids
        if len(repair_ids) != 1:
            result['domain'] = [('id', 'in', repair_ids)]
        elif len(repair_ids) == 1:
            res = self.env.ref('mrp_repair.view_repair_order_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = repair_ids[0]
        return result

    @api.multi
    def _get_rma_repaired_qty(self):
        self.ensure_one()
        qty = 0.0
        for repair in self.repair_ids.filtered(
                lambda p: p.state != 'cancel'):
            repair_qty = self.env['product.uom']._compute_qty_obj(
                self.uom_id,
                repair.product_qty,
                repair.product_uom,
            )
            qty += repair_qty
        return qty
