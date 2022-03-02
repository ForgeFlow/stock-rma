# Copyright (C) 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        res = super()._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        if "rma_line_id" in values:
            line = values.get("rma_line_id")
            res["rma_line_id"] = line.id
            if line.delivery_address_id:
                res["partner_id"] = line.delivery_address_id.id
            else:
                res["partner_id"] = line.rma_id.partner_id.id
            company_id = res["company_id"]
            company = self.env["res.company"].browse(company_id)
            cost = product_id.with_company(company).standard_price
            res["price_unit"] = cost
        return res
