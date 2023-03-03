# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.html)

{
    "name": "RMA Sale Force Invoiced",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "category": "RMA",
    "summary": "Forces sales orders created from RMA to be forced as invoiced",
    "author": "ForgeFlow",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["rma_sale", "sale_force_invoiced"],
    "data": [
        "views/rma_operation_views.xml",
    ],
    "installable": True,
}
