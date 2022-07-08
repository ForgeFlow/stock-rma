from odoo import models


class RmaLineMakeSaleOrder(models.TransientModel):
    _inherit = "rma.order.line.make.sale.order"

    def make_sale_order(self):
        res = super(RmaLineMakeSaleOrder, self).make_sale_order()
        split = res["domain"].split("[")
        split = split[2].split("]")
        sales_id = split[0].split(",")
        sales_id = self.env["sale.order"].browse([int(sales_id[0])])
        sales_id.only_confirm_if_all_products_are_available = True
        sales_id.propose_rule_on_available_quantity = True
        sales_id._onchange_propose_rule_on_available_quantity()
        return res
