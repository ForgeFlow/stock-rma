# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    "name": "RMA Account Unreconcile",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
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
