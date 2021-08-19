# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "RMA Website Delivery",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "summary": "Provide the return label to your customers",
    "author": "Open Source Integrators",
    "maintainer": "ForgeFlow",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["rma_website", "delivery"],
    "data": [
        "data/mail_template.xml",
        "views/stock_picking_view.xml",
    ],
    "maintainers": ["ursais"],
}
