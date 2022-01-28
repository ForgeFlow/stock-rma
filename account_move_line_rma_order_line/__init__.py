from . import models

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    aml_model = env["account.move.line"]
    sm_model = env["stock.move"]
    svl_model = env["stock.valuation.layer"]
    aml_moves = aml_model.search([("rma_line_id", "!=", False)])
    sm_moves = sm_model.search([("rma_line_id", "!=", False)])
    for account_move in aml_moves.mapped("move_id"):
        for aml_w_rma in account_move.invoice_line_ids.filtered(
            lambda x: x.product_id
            and x.account_id.id
            != x.product_id.categ_id.property_stock_valuation_account_id.id
            and x.rma_line_id
        ):
            invoice_lines_without_rma = account_move.invoice_line_ids.filtered(
                lambda x: x.product_id.id == aml_w_rma.product_id.id
                and not x.rma_line_id
                and aml_w_rma.name in x.name
            )
            if invoice_lines_without_rma:
                invoice_lines_without_rma.write(
                    {
                        "rma_line_id": aml_w_rma.rma_line_id.id,
                    }
                )
    for move in sm_moves:
        current_layers = svl_model.search([("stock_move_id", "=", move.id)])
        if current_layers:
            for aml in current_layers.mapped("account_move_id.line_ids").filtered(
                lambda x: x.account_id.id
                != move.product_id.categ_id.property_stock_valuation_account_id.id
            ):
                aml.rma_line_id = move.rma_line_id.id
