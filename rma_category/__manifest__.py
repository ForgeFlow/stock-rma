# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    "name": "RMA Category",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "category": "RMA",
    "summary": "Add RMA categories to classify RMAs",
    "author": "Akretion,ForgeFlow",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["rma"],
    "data": [
        "security/ir.model.access.csv",
        "views/rma_order_line.xml",
        "views/rma_category.xml",
    ],
    "installable": True,
}
