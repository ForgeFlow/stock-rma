# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models
from odoo.tools.float_utils import float_compare, float_is_zero


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_invoice_line_from_rma_line(self, line):
        data = super(AccountMove, self)._prepare_invoice_line_from_rma_line(line)
        if line.purchase_order_line_id:
            data["purchase_line_id"]: line.purchase_order_line_id.id
        return data

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self:
            rma_mls = move.line_ids.filtered(lambda l: l.rma_line_id)
            if rma_mls:
                # Try to reconcile the interim accounts for RMA lines
                rmas = rma_mls.mapped("rma_line_id")
                for rma in rmas:
                    product_accounts = (
                        rma.product_id.product_tmpl_id._get_product_accounts()
                    )
                    if rma.type == "customer":
                        product_interim_account = product_accounts["stock_output"]
                    else:
                        product_interim_account = product_accounts["stock_input"]
                    if product_interim_account.reconcile:
                        # Get the in and out moves
                        amls = self.env["account.move.line"].search(
                            [
                                ("rma_line_id", "=", rma.id),
                                ("account_id", "=", product_interim_account.id),
                                ("parent_state", "=", "posted"),
                                ("reconciled", "=", False),
                            ]
                        )
                        amls.reconcile()
        return res

    def _stock_account_prepare_anglo_saxon_in_lines_vals(self):
        lines_vals_list_rma = []
        rma_refunds = self.env["account.move"]
        price_unit_prec = self.env["decimal.precision"].precision_get("Product Price")
        for move in self:
            if (
                move.move_type != "in_refund"
                or not move.company_id.anglo_saxon_accounting
            ):
                continue
            move = move.with_company(move.company_id)
            for line in move.invoice_line_ids.filtered(lambda l: l.rma_line_id):
                if (
                    line.product_id.type != "product"
                    or line.product_id.valuation != "real_time"
                ):
                    continue
                # Retrieve accounts needed to generate the price difference.
                debit_pdiff_account = (
                    line.product_id.property_account_creditor_price_difference
                    or line.product_id.categ_id.property_account_creditor_price_difference_categ
                )
                debit_pdiff_account = move.fiscal_position_id.map_account(
                    debit_pdiff_account
                )
                if not debit_pdiff_account:
                    continue
                rma_line = line.rma_line_id
                valuation_price_unit = rma_line._get_price_unit()
                price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                price_unit_val_dif = price_unit - valuation_price_unit
                price_subtotal = line.quantity * price_unit_val_dif
                if (
                    not move.currency_id.is_zero(price_subtotal)
                    and not float_is_zero(
                        price_unit_val_dif, precision_digits=price_unit_prec
                    )
                    and float_compare(
                        line["price_unit"],
                        line.price_unit,
                        precision_digits=price_unit_prec,
                    )
                    == 0
                ):
                    # Add price difference account line.
                    vals = {
                        "name": line.name[:64],
                        "move_id": move.id,
                        "partner_id": line.partner_id.id
                        or move.commercial_partner_id.id,
                        "currency_id": line.currency_id.id,
                        "product_id": line.product_id.id,
                        "product_uom_id": line.product_uom_id.id,
                        "quantity": line.quantity,
                        "price_unit": price_unit_val_dif,
                        "price_subtotal": line.quantity * price_unit_val_dif,
                        "account_id": debit_pdiff_account.id,
                        "analytic_account_id": line.analytic_account_id.id,
                        "analytic_tag_ids": [(6, 0, line.analytic_tag_ids.ids)],
                        "exclude_from_invoice_tab": True,
                        "is_anglo_saxon_line": True,
                        "rma_line_id": line.rma_line_id.id,
                    }
                    vals.update(
                        line._get_fields_onchange_subtotal(
                            price_subtotal=vals["price_subtotal"]
                        )
                    )
                    lines_vals_list_rma.append(vals)

                    # Correct the amount of the current line.
                    vals = {
                        "name": line.name[:64],
                        "move_id": move.id,
                        "partner_id": line.partner_id.id
                        or move.commercial_partner_id.id,
                        "currency_id": line.currency_id.id,
                        "product_id": line.product_id.id,
                        "product_uom_id": line.product_uom_id.id,
                        "quantity": line.quantity,
                        "price_unit": -price_unit_val_dif,
                        "price_subtotal": line.quantity * -price_unit_val_dif,
                        "account_id": line.account_id.id,
                        "analytic_account_id": line.analytic_account_id.id,
                        "analytic_tag_ids": [(6, 0, line.analytic_tag_ids.ids)],
                        "exclude_from_invoice_tab": True,
                        "is_anglo_saxon_line": True,
                        "rma_line_id": line.rma_line_id.id,
                    }
                    vals.update(
                        line._get_fields_onchange_subtotal(
                            price_subtotal=vals["price_subtotal"]
                        )
                    )
                    lines_vals_list_rma.append(vals)
                    rma_refunds |= move
        lines_vals_list = super(
            AccountMove, self - rma_refunds
        )._stock_account_prepare_anglo_saxon_in_lines_vals()
        lines_vals_list += lines_vals_list_rma
        return lines_vals_list
