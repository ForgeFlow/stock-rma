# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import common


class TestRmaQualityControlIssue(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestRmaQualityControlIssue, cls).setUpClass()

        cls.rma_obj = cls.env['rma.order']
        cls.rma_line_obj = cls.env['rma.order.line']
        cls.rma_op_obj = cls.env['rma.operation']
        cls.qc_issue_obj = cls.env['qc.issue']
        cls.product = cls.env['product.product']
        cls.partner = cls.env['res.partner']
        cls.res_users = cls.env['res.users']
        cls.company = cls.env.ref('base.main_company')

        cls.rma_route_cust = cls.env.ref('rma.route_rma_customer')

        # Create User and Group
        cls.group_user = cls.env.ref(
            'base.group_user')
        cls.user = cls._create_user('no_bi_user', cls.group_user,
                                    cls.company)

        # Create customer
        cls.supplier1 = cls.partner.create({'name': 'Supplier 1'})

        # Create product
        cls.product_1 = cls.product.create({
            'name': 'Test Product 1',
            'type': 'product',
            'list_price': 100.0,
        })

        # Create RMA group and operation:
        cls.rma_group = cls.rma_obj.create({
            'partner_id': cls.supplier1.id,
        })

    @classmethod
    def _create_user(self, login, groups, company):
        """Create a user."""
        user = self.res_users.create({
            'name': login,
            'login': login,
            'password': 'demo',
            'email': 'example@yourcompany.com',
            'company_id': company.id,
            'groups_id': [(6, 0, groups.ids)]
        })
        return user

    @classmethod
    def _create_qc_issue(self):
        qc_issue_id = self.env['qc.issue'].create({
            'product_id': self.product_1.id,
            'product_qty': 1.0,
            'inspector_id': self.user.id,
            'product_uom': self.product_1.uom_id.id,
        })
        qc_issue_id._compute_rma_line_count()
        qc_issue_id.action_view_rma_lines_supplier()
        qc_issue_id.action_view_rma_lines_customer()
        return qc_issue_id

    def test_01_add_from_sale_order(self):
        """Test wizard to create RMA from QC Issue."""
        self.rma_qc_issue_item = self.env[
            'qc.issue.make.supplier.rma.item']
        self.rma_qc_issue = self.env['qc.issue.make.supplier.rma']

        qc_issue = self.rma_qc_issue.with_context({
            'active_ids': self.rma_group.rma_line_ids.ids,
            'active_model': 'qc.issue',
            'active_id': 1
        }).create({
            'partner_id': self.supplier1.id,
            'supplier_rma_id': self.rma_group.id,
            'use_group': True,
            'item_ids': [(0, 0, {
                'issue_id': self._create_qc_issue().id,
                'product_id': self.product_1.id,
                'name': 'Test RMA Refund',
                'product_qty': 1.0,
                'uom_id': self.product_1.uom_id.id
            })]})
        self.rma_qc_issue.with_context({
            'active_ids': self._create_qc_issue().ids,
            'active_model': 'qc.issue'
        }).default_get([str(qc_issue.id)])
        qc_issue.make_supplier_rma()
