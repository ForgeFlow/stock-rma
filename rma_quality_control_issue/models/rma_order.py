# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    qc_issue_id = fields.Many2one(
        comodel_name="qc.issue", string="Originating QC Issue",
        copy=False, readonly=True,
    )
