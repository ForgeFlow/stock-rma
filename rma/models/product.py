# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    rma_operation_id = fields.Many2one(
        comodel_name="rma.operation", string="RMA Operation")
    rma_approval_policy = fields.Selection(
        related="categ_id.rma_approval_policy", readonly=True)
