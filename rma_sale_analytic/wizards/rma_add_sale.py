# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class RmaAddSale(models.TransientModel):
    _inherit = 'rma_add_sale'

    @api.model
    def _prepare_rma_line_from_sale_order_line(self, line):
        data = super(RmaAddSale, self).\
            _prepare_rma_line_from_sale_order_line(line)
        data.update(analytic_account_id=line.analytic_account_id.id)
        return data
