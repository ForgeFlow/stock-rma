# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)


from odoo.tests.common import TransactionCase


class TestRmaAccountUnreconciled(TransactionCase):
    def setUp(self):
        super().setUp()
