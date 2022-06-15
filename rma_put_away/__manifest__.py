{
    "name": "RMA Put Away",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "category": "RMA",
    "summary": "Allows to put away the received products"
    "in odoo",
    "author": "ForgeFlow",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["rma"],
    "data": [
        "views/rma_put_away_view.xml",
        "views/rma_operation_view.xml",
        "views/rma_order_view.xml",
        "views/rma_order_line_view.xml",
    ],
    "installable": True,
}
