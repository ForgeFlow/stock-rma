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

        cls.rma_qc_issue_item = cls.env[
            'qc.issue.make.supplier.rma.item']
        cls.rma_qc_issue = cls.env['qc.issue.make.supplier.rma']

        cls.rma_route_cust = cls.env.ref('rma.route_rma_customer')

        # Root User
        cls.admin_user = cls.env.ref('base.user_root')

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
    def _create_qc_issue(self):
        qc_issue_id = \
            self.qc_issue_obj.sudo(self.admin_user.id).create({
                'product_id': self.product_1.id,
                'product_qty': 1.0,
                'inspector_id': self.admin_user.id,
                'product_uom': self.product_1.uom_id.id,
            })

        qc_issue_id._compute_rma_line_count()
        qc_issue_id.action_view_rma_lines_supplier()
        qc_issue_id.action_view_rma_lines_customer()
        return qc_issue_id

    def test_01_add_from_qc_issue(self):
        """Test wizard to create RMA from QC Issue."""

        # Create the QC Issue
        qc_issue = self._create_qc_issue()

        # Wizard to create Supplier RMA from QC Issue
        wiz = self.rma_qc_issue.with_context({
            'active_ids': self.rma_group.rma_line_ids.ids,
            'active_model': 'qc.issue',
            'active_id': qc_issue.id,
        }).create({
            'partner_id': self.supplier1.id,
            'use_group': False,
            'item_ids': [(0, 0, {
                'issue_id': qc_issue.id,
                'product_id': self.product_1.id,
                'name': 'Test RMA Refund',
                'product_qty': 1.0,
                'uom_id': self.product_1.uom_id.id
            })]})
        self.rma_qc_issue.with_context({
            'active_ids': qc_issue.ids,
            'active_model': 'qc.issue'
        }).default_get([str(wiz.id)])
        wiz.make_supplier_rma()

        # Check if RMA Supplier count has increased in QC Issue
        self.assertEqual(qc_issue.rma_line_count_supplier, 1,
                         'The count for rma supplier should be equal to 1')
