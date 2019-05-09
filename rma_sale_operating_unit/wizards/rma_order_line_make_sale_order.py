# -*- coding: utf-8 -*-
# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models, api


class RmaLineMakeSaleOrder(models.TransientModel):
    _inherit = "rma.order.line.make.sale.order"

    @api.model
    def _prepare_sale_order(self, line):
        sale_line = super(
            RmaLineMakeSaleOrder, self)._prepare_sale_order(line)
        sale_line.update(operating_unit_id=line.operating_unit_id.id)
        team = self.env['crm.team'].search(
            [('operating_unit_id', '=', line.operating_unit_id.id)], limit=1)
        sale_line.update(team_id=team.id)
        return sale_line
