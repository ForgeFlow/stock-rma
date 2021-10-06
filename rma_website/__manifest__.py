# Copyright (C) 2021 Open Source Integrators (https://www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "RMA Website",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "summary": "Allow Portal users to create RMA",
    "author": "Open Source Integrators",
    "maintainer": "ForgeFlow",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["portal", "utm", "rma_account"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir.rule.csv",
        "views/portal_view.xml",
        "views/assets.xml",
    ],
    "maintainers": ["ursais"],
}
