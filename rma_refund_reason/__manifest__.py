# Copyright (C) 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "RMA Refund Reason Integration",
    "version": "14.0.1.0.0",
    "summary": "RMA Refund Reason Integration",
    "category": "RMA",
    "author": "ForgeFlow S.L.",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "license": "AGPL-3",
    "depends": ["rma_account", "account_invoice_refund_reason"],
    "data": [
        "views/rma_operation_view.xml",
        "views/rma_order_line_view.xml",
    ],
    "installable": True,
    "auto_install": True,
}
