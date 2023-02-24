# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "RMA Repair",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "category": "RMA",
    "summary": "Links RMA with Repairs.",
    "author": "ForgeFlow",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["rma_account", "repair"],
    "data": [
        "security/ir.model.access.csv",
        "views/rma_order_view.xml",
        "views/rma_operation_view.xml",
        "views/repair_view.xml",
        "wizards/rma_order_line_make_repair_view.xml",
        "views/rma_order_line_view.xml",
        "data/repair_sequence.xml",
    ],
    "installable": True,
}
