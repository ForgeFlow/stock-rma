# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Operating Unit in RMA Orders",
    "version": "9.0.1.0.0",
    "author": "Eficent",
    "license": "LGPL-3",
    "website": "http://www.eficent.com",
    "category": "Operating Units",
    "depends": ["rma", "operating_unit"],
    "data": [
        "security/rma_security.xml",
        "views/rma_order_view.xml"
    ],
    'installable': True,
}
