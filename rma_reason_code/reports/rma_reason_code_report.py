# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class RmaReasonCodeReport(models.Model):
    _name = "rma.reason.code.report"
    _auto = False
    _description = "Rma Reason Code Report"

    rma_order_line_id = fields.Many2one(comodel_name="rma.order.line")
    reason_code_id = fields.Many2one(comodel_name="rma.reason.code")
    date_rma = fields.Datetime(string="Order Date")
    type = fields.Selection([("customer", "Customer"), ("supplier", "Supplier")])
    company_id = fields.Many2one(comodel_name="res.company")

    def _select(self):
        return """
            SELECT
                row_number() OVER () AS id,
                rma.id as rma_order_line_id,
                rma.type,
                rrc.id as reason_code_id,
                rma.date_rma,
                rma.company_id

        """

    def _from(self):
        return """
            FROM
                rma_order_line rma
                INNER JOIN
                    rma_order_line_reason_code_rel rolr ON rma.id = rolr.rma_order_line_id
                INNER JOIN
                    rma_reason_code rrc ON rolr.rma_reason_code_id = rrc.id

        """

    def _order_by(self):
        return """
            ORDER BY
                rma.id, rrc.id
        """

    @property
    def _table_query(self):
        return """
            {_select}
            {_from}
            {_order_by}
        """.format(
            _select=self._select(), _from=self._from(), _order_by=self._order_by()
        )
