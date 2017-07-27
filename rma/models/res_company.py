# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    rma_rule_id = fields.Many2one('rma.rule', 'Default RMA Approval Policy')
