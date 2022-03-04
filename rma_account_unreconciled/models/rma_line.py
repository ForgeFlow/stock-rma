# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.osv import expression


class RmaOrderLine(models.Model):

    _inherit = "rma.order.line"

    unreconciled = fields.Boolean(
        compute="_compute_unreconciled",
        search="_search_unreconciled",
        help="Indicates that a Purchase Order has related Journal items not "
        "reconciled.\nNote that if it is false it can be either that "
        "everything is reconciled or that the related accounts do not "
        "allow reconciliation",
    )

    def _compute_unreconciled(self):
        acc_item = self.env["account.move.line"]
        for rec in self:
            domain = rec._get_rma_unreconciled_base_domain()
            unreconciled_domain = expression.AND(
                [domain, [("rma_line_id", "=", rec.id)]]
            )
            unreconciled_items = acc_item.search(unreconciled_domain)
            rec.unreconciled = len(unreconciled_items) > 0

    def _search_unreconciled(self, operator, value):
        if operator != "=" or not isinstance(value, bool):
            raise ValueError(_("Unsupported search operator"))
        acc_item = self.env["account.move.line"]
        domain = self._get_rma_unreconciled_base_domain()
        unreconciled_domain = expression.AND([domain, [("rma_line_id", "!=", False)]])
        unreconciled_items = acc_item.search(unreconciled_domain)
        unreconciled_pos = unreconciled_items.mapped("rma_line_id")
        if value:
            return [("id", "in", unreconciled_pos.ids)]
        else:
            return [("id", "not in", unreconciled_pos.ids)]

    @api.model
    def _get_rma_unreconciled_base_domain(self):
        categories = self.env["product.category"].search(
            [("property_valuation", "=", "real_time")]
        )
        included_accounts = (
            categories.mapped("property_stock_account_input_categ_id").ids
        ) + (categories.mapped("property_stock_account_output_categ_id").ids)
        unreconciled_domain = [
            ("account_id.reconcile", "=", True),
            ("account_id", "in", included_accounts),
            ("move_id.state", "=", "posted"),
            # for some reason when amount_residual is zero
            # is marked as reconciled, this is better check
            ("full_reconcile_id", "=", False),
            ("company_id", "in", self.env.companies.ids),
        ]
        return unreconciled_domain

    def action_view_unreconciled(self):
        self.ensure_one()
        acc_item = self.env["account.move.line"]
        domain = self._get_rma_unreconciled_base_domain()
        unreconciled_domain = expression.AND([domain, [("rma_line_id", "=", self.id)]])
        unreconciled_items = acc_item.search(unreconciled_domain)
        action = self.env.ref("account.action_account_moves_all")
        action_dict = action.read()[0]
        action_dict["domain"] = [("id", "in", unreconciled_items.ids)]
        return action_dict

    def action_open_reconcile(self):
        aml_model = self.env["account.move.line"]
        action = self.action_view_unreconciled()
        amls = (
            action.get("domain") and aml_model.search(action.get("domain")) or aml_model
        )
        accounts = amls.mapped("account_id")
        action_context = {
            "show_mode_selector": False,
            "account_ids": accounts.ids,
            "active_model": "account.move.line",
            "active_ids": amls.ids,
        }
        return {
            "type": "ir.actions.client",
            "tag": "manual_reconciliation_view",
            "context": action_context,
        }
