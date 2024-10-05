# Copyright 2019-23 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
{
    "name": "RMA Kanban Stages",
    "summary": "Stages on RMA",
    "version": "16.0.1.0.0",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "author": "ForgeFlow",
    "depends": [
        "rma",
        "base_kanban_stage",
    ],
    "data": [
        "data/rma_kanban_stage.xml",
        "views/rma_order_line_view.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
}
