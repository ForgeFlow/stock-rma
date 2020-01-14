# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def _compute_rma_line_count(self):
        for rec in self:
            rec.rma_line_count = len(rec.rma_line_ids)

    rma_line_ids = fields.One2many(
        comodel_name="rma.order.line", string="RMAs", inverse_name="partner_id"
    )
    rma_line_count = fields.Integer(compute="_compute_rma_line_count")

    @api.multi
    def action_open_partner_rma(self):
        action = self.env.ref("rma.action_rma_customer_lines")
        result = action.read()[0]
        result["context"] = {"search_default_partner_id": self.id}
        return result
