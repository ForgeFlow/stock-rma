# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import _, api, fields, models
from openerp.addons import decimal_precision as dp
from openerp.exceptions import UserError


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.model
    def _default_invoice_address(self):
        partner_id = self.env.context.get('partner_id', False)
        if partner_id:
            return self.env['res.partner'].browse(partner_id)
        return False

    @api.multi
    @api.depends('refund_line_ids', 'refund_line_ids.invoice_id.state',
                 'refund_policy', 'type')
    def _compute_qty_refunded(self):
        for rec in self:
            rec.qty_refunded = sum(rec.refund_line_ids.filtered(
                lambda i: i.invoice_id.state in ('open', 'paid')).mapped(
                'quantity'))

    @api.one
    @api.depends('refund_line_ids', 'refund_line_ids.invoice_id.state',
                 'refund_policy', 'move_ids', 'move_ids.state', 'type')
    def _compute_qty_to_refund(self):
        qty = 0.0
        if self.refund_policy == 'ordered':
            qty = self.product_qty - self.qty_refunded
        elif self.refund_policy == 'received':
            qty = self.qty_received - self.qty_refunded
        self.qty_to_refund = qty

    @api.multi
    def _compute_refund_count(self):
        for rec in self:
            rec.refund_count = len(rec.refund_line_ids.mapped('invoice_id'))

    invoice_address_id = fields.Many2one(
        'res.partner', string='Partner invoice address',
        default=_default_invoice_address,
        help="Invoice address for current rma order.")

    refund_count = fields.Integer(compute=_compute_refund_count,
                                  string='# of Refunds', copy=False, default=0)

    invoice_line_id = fields.Many2one('account.invoice.line',
                                      string='Invoice Line',
                                      ondelete='restrict',
                                      index=True)
    refund_line_ids = fields.One2many(comodel_name='account.invoice.line',
                                      inverse_name='rma_line_id',
                                      string='Refund Lines',
                                      copy=False, index=True, readonly=True)
    invoice_id = fields.Many2one('account.invoice', string='Source',
                                 related='invoice_line_id.invoice_id',
                                 index=True, readonly=True)
    refund_policy = fields.Selection([
        ('no', 'No refund'), ('ordered', 'Based on Ordered Quantities'),
        ('received', 'Based on Received Quantities')], string="Refund Policy",
        required=True, default='no')
    qty_to_refund = fields.Float(
        string='Qty To Refund', copy=False,
        digits=dp.get_precision('Product Unit of Measure'), readonly=True,
        compute=_compute_qty_to_refund, store=True)
    qty_refunded = fields.Float(
        string='Qty Refunded', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True, compute=_compute_qty_refunded, store=True)

    @api.onchange('operation_id')
    def _onchange_operation_id(self):
        result = super(RmaOrderLine, self)._onchange_operation_id()
        if not self.operation_id:
            return result
        self.refund_policy = self.operation_id.refund_policy
        return result

    @api.onchange('invoice_line_id')
    def _onchange_invoice_line_id(self):
        result = {}
        if not self.invoice_line_id:
            return result
        self.origin = self.invoice_id.number
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
        invoice_ids = []
        for inv_line in self.refund_line_ids:
            invoice_ids.append(inv_line.invoice_id.id)
        # choose the view_mode accordingly
        if len(invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(invoice_ids) + ")]"
        elif len(invoice_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = invoice_ids[0]
        return result
