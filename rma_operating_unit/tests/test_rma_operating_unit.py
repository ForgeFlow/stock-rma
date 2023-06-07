# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from openerp.tests import common


class TestRmaOperatingUnit(common.TransactionCase):

    def setUp(self):
        super(TestRmaOperatingUnit, self).setUp()
        self.res_users_model = self.env['res.users']
        self.rma_model = self.env['rma.order']

        self.company = self.env.ref('base.main_company')
        self.partner = self.env.ref('base.res_partner_1')
        self.grp_rma_manager = self.env.ref('rma.group_rma_manager')

        # Main Operating Unit
        self.main_OU = self.env.ref('operating_unit.main_operating_unit')
        # B2C Operating Unit
        self.b2c_OU = self.env.ref('operating_unit.b2c_operating_unit')

        # Users
        self.user1 = self._create_user('user_1',
                                       [self.grp_rma_manager],
                                       self.company,
                                       [self.main_OU, self.b2c_OU])
        self.user2 = self._create_user('user_2',
                                       [self.grp_rma_manager],
                                       self.company,
                                       [self.b2c_OU])
        self.user3 = self._create_user('user_3',
                                       [self.grp_rma_manager],
                                       self.company,
                                       [self.main_OU, self.b2c_OU])

        # RMA Orders
        self.rma_order1 = self._create_rma(self.user1.id, self.main_OU)
        self.rma_order2 = self._create_rma(self.user2.id, self.b2c_OU)
        self.rma_order3 = self._create_rma(self.user3.id)

    def _create_user(self, login, groups, company, operating_units):
        """Creates a user."""
        group_ids = [group.id for group in groups]
        user = self.res_users_model.create({
            'name': login,
            'login': login,
            'password': 'demo',
            'email': 'example@yourcompany.com',
            'company_id': company.id,
            'company_ids': [(4, company.id)],
            'operating_unit_ids': [(4, ou.id) for ou in operating_units],
            'groups_id': [(6, 0, group_ids)]
        })
        return user

    def _create_rma(self, uid, operating_unit=False):
        """Creates an RMA"""
        if not operating_unit:
            operating_unit = self.rma_model.sudo(uid).\
                _default_operating_unit()
        rma_order = self.rma_model.sudo(uid).create({
            'operating_unit_id': operating_unit.id,
            'partner_id': self.partner.id,
            'user_id': uid,
            })
        return rma_order

    def test_security(self):
        # User 2 is only assigned to Operating Unit B2C, and cannot
        # access RMA of Main Operating Unit.
        record = self.rma_model.sudo(
            self.user2.id).search([('id', '=', self.rma_order1.id),
                                   ('operating_unit_id', '=',
                                    self.main_OU.id)])
        self.assertEqual(record.ids, [], 'User 2 should not have access to '
                         'OU %s.' % self.main_OU.name)
