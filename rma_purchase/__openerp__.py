# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
{
    'name': 'RMA Purchase',
    'version': '9.0.1.0.0',
    'category': 'RMA',
    'summary': 'RMA from PO',
    'description': """
    RMA from PO
""",
    'author': 'Eficent',
    'website': 'http://www.github.com/OCA/rma',
    'depends': ['rma_account', 'purchase'],
    'data': ['views/rma_order_view.xml',
             'views/rma_order_line_view.xml',
             'wizards/rma_add_purchase.xml'],
    'installable': True,
    'auto_install': True,
}
