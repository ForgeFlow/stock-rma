# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import api, fields, models


class MrpRepair(models.Model):
    _inherit = "mrp.repair"

    rma_line_id = fields.Many2one(
        comodel_name='rma.order.line', string='RMA', ondelete='restrict')
