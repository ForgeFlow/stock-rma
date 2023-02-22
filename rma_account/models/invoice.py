# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.depends('invoice_line_ids.rma_line_ids')
    def _compute_rma_count(self):
        for inv in self:
            rmas = self.mapped('invoice_line_ids.rma_line_ids')
            inv.rma_count = len(rmas)

    def _prepare_invoice_line_from_rma_line(self, line):
        qty = line.qty_to_refund
        if float_compare(
                qty, 0.0, precision_rounding=line.uom_id.rounding) <= 0:
            qty = 0.0
        # Todo fill taxes from somewhere
        invoice_line = self.env['account.invoice.line']
        data = {
            'purchase_line_id': line.id,
            'name': line.name + ': '+line.name,
            'origin': line.origin,
            'uom_id': line.uom_id.id,
            'product_id': line.product_id.id,
            'account_id': invoice_line.with_context(
                {'journal_id': self.journal_id.id,
                 'type': 'in_invoice'})._default_account(),
            'price_unit': line.company_id.currency_id.with_context(
                date=self.date_invoice).compute(
                line.price_unit, self.currency_id, round=False),
            'quantity': qty,
            'discount': 0.0,
            'account_analytic_id': line.analytic_account_id.id,
            'rma_line_ids': [(4, line.id)],
        }
        return data

    @api.onchange('add_rma_line_id')
    def on_change_add_rma_line_id(self):
        if not self.add_rma_line_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.add_rma_line_id.partner_id.id

        new_line = self.env['account.invoice.line']
        if self.add_rma_line_id not in (
                self.invoice_line_ids.mapped('rma_line_id')):
            data = self._prepare_invoice_line_from_rma_line(
                self.add_rma_line_id)
            new_line = new_line.new(data)
            new_line._set_additional_fields(self)
        self.invoice_line_ids += new_line
        self.add_rma_line_id = False
        return {}

    rma_count = fields.Integer(
        compute=_compute_rma_count, string='# of RMA')

    add_rma_line_id = fields.Many2one(
        comodel_name='rma.order.line',
        string="Add from RMA line",
        ondelete="set null",
        help="Create a refund in based on an existing rma_line")

    @api.multi
    def action_view_rma_supplier(self):
        action = self.env.ref('rma.action_rma_supplier_lines')
        result = action.read()[0]
        rma_list = self.mapped('invoice_line_ids.rma_line_ids').ids
        # choose the view_mode accordingly
        if len(rma_list) != 1:
            result['domain'] = [('id', 'in', rma_list)]
        elif len(rma_list) == 1:
            res = self.env.ref('rma.view_rma_line_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = rma_list[0]
        return result

    @api.multi
    def action_view_rma_customer(self):
        action = self.env.ref('rma.action_rma_customer_lines')
        result = action.read()[0]
        rma_list = self.mapped('invoice_line_ids.rma_line_ids').ids
        # choose the view_mode accordingly
        if len(rma_list) != 1:
            result['domain'] = [('id', 'in', rma_list)]
        elif len(rma_list) == 1:
            res = self.env.ref('rma.view_rma_line_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = rma_list[0]
        return result


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.multi
    def _compute_rma_count(self):
        for invl in self:
            rma_lines = invl.mapped('rma_line_ids')
            invl.rma_line_count = len(rma_lines)

    rma_line_count = fields.Integer(
        compute=_compute_rma_count, string='# of RMA')
    rma_line_ids = fields.One2many(
        comodel_name='rma.order.line', inverse_name='invoice_line_id',
        string="RMA", readonly=True,
        help="This will contain the RMA lines for the invoice line")

    rma_line_id = fields.Many2one(
        comodel_name='rma.order.line',
        string="RMA line refund",
        ondelete="set null",
        help="This will contain the rma line that originated the refund line")
