# Copyright 2024 Akretion
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    "name": "RMA Product Exchange",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "category": "RMA",
    "summary": "Manage RMA for product exchange",
    "author": "Akretion, ForgeFlow",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": [
        "rma",
    ],
    "data": [
        "views/rma_order_view.xml",
        "views/rma_operation_view.xml",
        "views/rma_order_line_view.xml",
    ],
    "installable": True,
}
