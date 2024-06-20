# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "RMA Account Unreconcile",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "category": "RMA",
    "summary": "Integrates RMA with Invoice Processing",
    "author": "ForgeFlow",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["account_move_line_rma_order_line", "rma"],
    "data": [
        "views/rma_line_view.xml",
    ],
    "installable": True,
}
