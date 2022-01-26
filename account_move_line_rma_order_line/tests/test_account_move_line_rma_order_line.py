# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L. (www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestAccountMoveLineRmaOrderLine(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountMoveLineRmaOrderLine, cls).setUpClass()
        cls.rma_model = cls.env['rma.order']
        cls.rma_line_model = cls.env['rma.order.line']
        cls.rma_add_stock_move = cls.env['rma_add_stock_move']
        cls.rma_make_picking = cls.env['rma_make_picking.wizard']
        cls.invoice_model = cls.env['account.invoice']
        cls.stock_picking_model = cls.env['stock.picking']
        cls.invoice_line_model = cls.env['account.invoice.line']
        cls.product_model = cls.env['product.product']
        cls.product_ctg_model = cls.env['product.category']
        cls.acc_type_model = cls.env['account.account.type']
        cls.account_model = cls.env['account.account']
        cls.aml_model = cls.env['account.move.line']
        cls.res_users_model = cls.env['res.users']

        cls.partner1 = cls.env.ref('base.res_partner_1')
        cls.location_stock = cls.env.ref('stock.stock_location_stock')
        cls.company = cls.env.ref('base.main_company')
        cls.group_rma_user = cls.env.ref('rma.group_rma_customer_user')
        cls.group_account_invoice = cls.env.ref(
            'account.group_account_invoice')
        cls.group_account_manager = cls.env.ref(
            'account.group_account_manager')
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        wh = cls.env.ref('stock.warehouse0')
        cls.stock_rma_location = wh.lot_rma_id
        cls.customer_location = cls.env.ref(
            'stock.stock_location_customers')
        cls.supplier_location = cls.env.ref(
            'stock.stock_location_suppliers')
        # Create account for Goods Received Not Invoiced
        acc_type = cls._create_account_type('equity', 'other')
        name = 'Goods Received Not Invoiced'
        code = 'grni'
        cls.account_grni = cls._create_account(
            acc_type, name, code,cls.company)

        # Create account for Cost of Goods Sold
        acc_type = cls._create_account_type('expense', 'other')
        name = 'Cost of Goods Sold'
        code = 'cogs'
        cls.account_cogs = cls._create_account(
            acc_type, name, code, cls.company)
        # Create account for Inventory
        acc_type = cls._create_account_type('asset', 'other')
        name = 'Inventory'
        code = 'inventory'
        cls.account_inventory = cls._create_account(
            acc_type, name, code, cls.company)
        # Create Product
        cls.product = cls._create_product()
        cls.product_uom_id = cls.env.ref('product.product_uom_unit')
        # Create users
        cls.rma_user = cls._create_user(
            'rma_user', [cls.group_rma_user,
                         cls.group_account_invoice], cls.company)
        cls.account_invoice = cls._create_user(
            'account_invoice', [cls.group_account_invoice], cls.company)
        cls.account_manager = cls._create_user(
            'account_manager', [cls.group_account_manager], cls.company)

    @classmethod
    def _create_user(cls, login, groups, company):
        """ Create a user."""
        group_ids = [group.id for group in groups]
        user = \
            cls.res_users_model.with_context(
                {'no_reset_password': True}).create({
                    'name': 'Test User',
                    'login': login,
                    'password': 'demo',
                    'email': 'test@yourcompany.com',
                    'company_id': company.id,
                    'company_ids': [(4, company.id)],
                    'groups_id': [(6, 0, group_ids)]
                })
        return user.id

    @classmethod
    def _create_account_type(cls, name, type):
        acc_type = cls.acc_type_model.create({
            'name': name,
            'type': type
        })
        return acc_type

    @classmethod
    def _create_account(cls, acc_type, name, code, company):
        """Create an account."""
        account = cls.account_model.create({
            'name': name,
            'code': code,
            'user_type_id': acc_type.id,
            'company_id': company.id
        })
        return account

    @classmethod
    def _create_product(cls):
        """Create a Product."""
        #        group_ids = [group.id for group in groups]
        product_ctg = cls.product_ctg_model.create({
            'name': 'test_product_ctg',
            'property_stock_valuation_account_id': cls.account_inventory.id,
            'property_valuation': 'real_time',
            'property_stock_account_input_categ_id': cls.account_grni.id,
            'property_stock_account_output_categ_id': cls.account_cogs.id,
        })
        product = cls.product_model.create({
            'name': 'test_product',
            'categ_id': product_ctg.id,
            'type': 'product',
            'standard_price': 1.0,
            'list_price': 1.0,
        })
        return product

    @classmethod
    def _create_picking(cls, partner):
        return cls.stock_picking_model.create({
            'partner_id': partner.id,
            'picking_type_id': cls.env.ref('stock.picking_type_in').id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.supplier_location.id
            })

    @classmethod
    def _prepare_move(cls, product, qty, src, dest, picking_in):
        res = {
            'partner_id': cls.partner1.id,
            'product_id': product.id,
            'name': product.partner_ref,
            'state': 'confirmed',
            'product_uom': cls.product_uom_id.id or product.uom_id.id,
            'product_uom_qty': qty,
            'origin': 'Test RMA',
            'location_id': src.id,
            'location_dest_id': dest.id,
            'picking_id': picking_in.id
        }
        return res

    @classmethod
    def _create_rma(cls, products2move, partner):
        picking_in = cls._create_picking(partner)
        moves = []
        for item in products2move:
            move_values = cls._prepare_move(
                item[0], item[1], cls.stock_location,
                cls.customer_location, picking_in)
            moves.append(cls.env['stock.move'].create(move_values))

        rma_id = cls.rma_model.create(
            {
                'reference': '0001',
                'type': 'customer',
                'partner_id': partner.id,
                'company_id': cls.env.ref('base.main_company').id
            })
        for move in moves:
            wizard = cls.rma_add_stock_move.with_context(
                {'stock_move_id': move.id, 'customer': True,
                 'active_ids': rma_id.id,
                 'active_model': 'rma.order',
                 }
            ).create({})
            data = wizard._prepare_rma_line_from_stock_move(move)
            wizard.add_lines()

            for operation in move.product_id.rma_customer_operation_id:
                operation.in_route_id = False
            move.product_id.categ_id.rma_customer_operation_id = False
            move.product_id.rma_customer_operation_id = False
            wizard._prepare_rma_line_from_stock_move(move)
            cls.line = cls.rma_line_model.create(data)
        return rma_id

    def _get_balance(self, domain):
        """
        Call read_group method and return the balance of particular account.
        """
        aml_rec = self.aml_model.read_group(
            domain, ['debit', 'credit', 'account_id'], ['account_id'])
        if aml_rec:
            return aml_rec[0].get('debit', 0) - aml_rec[0].get('credit', 0)
        else:
            return 0.0

    def _check_account_balance(self, account_id, rma_line=None,
                               expected_balance=0.0):
        """
        Check the balance of the account
        """
        domain = [('account_id', '=', account_id)]
        if rma_line:
            domain.extend([('rma_line_id', '=', rma_line.id)])

        balance = self._get_balance(domain)
        if rma_line:
            self.assertEqual(balance, expected_balance,
                             'Balance is not %s for rma Line %s.'
                             % (str(expected_balance), rma_line.name))

    def test_rma_invoice(self):
        """Test that the rma line moves from the rma order to the
        account move line and to the invoice line.
        """
        products2move = [(self.product, 1), ]
        rma = self._create_rma(products2move, self.partner1)
        rma_line = rma.rma_line_ids[0]
        rma_line.action_rma_approve()
        wizard = self.rma_make_picking.with_context({
            'active_id': 1,
            'active_ids': rma.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'incoming',
        }).create({})
        procurements = wizard._create_picking()
        group_ids = set([proc.group_id.id for proc in procurements if
                         proc.group_id])
        domain = [('group_id', 'in', list(group_ids))]
        picking = self.stock_picking_model.search(domain)
        picking.action_assign()
        picking.do_transfer()

        expected_balance = 1.0
        self._check_account_balance(self.account_inventory.id,
                                    rma_line=rma_line,
                                    expected_balance=expected_balance)

        invoice = self.invoice_model.create({
            'partner_id': self.partner1.id,
            'rma_id': rma.id,
            'account_id': rma.partner_id.property_account_payable_id.id,
        })
        invoice.signal_workflow('invoice_open')

        for aml in invoice.move_id.line_ids:
            if aml.product_id == rma_line.product_id and aml.invoice_id:
                self.assertEqual(aml.rma_line_id, rma_line,
                                'Rma Order line has not been copied '
                                'from the invoice to the account move line.')
