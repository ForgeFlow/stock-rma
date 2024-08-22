# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    'name': 'RMA Sale',
    'version': '10.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'RMA',
    'summary': 'Links RMA with Sales Orders',
    'author': "Eficent",
    'website': 'http://www.github.com/OCA/rma',
    'depends': ['rma_account', 'sale_stock'],
    'data': ['views/rma_order_view.xml',
             'views/rma_operation_view.xml',
             'views/sale_order_view.xml',
             'wizards/rma_order_line_make_sale_order_view.xml',
             'wizards/rma_add_sale.xml',
             'views/rma_order_line_view.xml'],
    'installable': True,
    'auto_install': True,
}
