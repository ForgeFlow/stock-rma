# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.depends('invoice_line_ids.rma_line_ids')
    def _compute_rma_count(self):
        for inv in self:
            rmas = self.mapped('invoice_line_ids.rma_line_ids')
            inv.rma_count = len(rmas)

    rma_count = fields.Integer(
        compute=_compute_rma_count, string='# of RMA')

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
