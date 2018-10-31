# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import common


class TestRmaAnalytic(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestRmaAnalytic, cls).setUpClass()
        cls.stock_picking_model = cls.env['stock.picking']
        cls.rma_line_model = cls.env['rma.order.line']
        cls.rma_model = cls.env['rma.order']
        cls.rma_add_stock_move = cls.env['rma_add_stock_move']
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.product_1 = cls.env.ref('product.product_product_25')
        cls.customer_location = cls.env.ref(
            'stock.stock_location_customers')
        cls.product_uom_id = cls.env.ref('product.product_uom_unit')
        products2move = [(cls.product_1, 3), ]
        cls.analytic_1 = cls.env['account.analytic.account'].create({
            'name': 'Test account #1',
        })
        cls.partner_id = cls.env.ref('base.res_partner_1')
        cls.rma_ana_id = cls._create_rma_analytic(
            products2move, cls.partner_id)

    @classmethod
    def _create_picking(cls, partner):
        return cls.stock_picking_model.create({
            'partner_id': partner.id,
            'picking_type_id': cls.env.ref('stock.picking_type_in').id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id
            })

    @classmethod
    def _prepare_anal_move(cls, product, qty, src, dest, picking_in, analytic):
        res = {
            'partner_id': cls.partner_id.id,
            'product_id': product.id,
            'name': product.partner_ref,
            'state': 'confirmed',
            'product_uom': cls.product_uom_id.id or product.uom_id.id,
            'product_uom_qty': qty,
            'origin': 'Test RMA',
            'location_id': src.id,
            'location_dest_id': dest.id,
            'picking_id': picking_in.id,
            'analytic_account_id': analytic.id,
        }
        return res

    @classmethod
    def _create_rma_analytic(cls, products2move, partner):
        picking_in = cls._create_picking(partner)
        moves = []
        for item in products2move:
            move_values = cls._prepare_anal_move(
                item[0], item[1], cls.stock_location,
                cls.customer_location, picking_in, cls.analytic_1)
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

    def test_analytic(cls):
        for line in cls.rma_ana_id.rma_line_ids:
            for move in line.move_ids:
                cls.assertEqual(
                    line.analytic_account_id, move.analytic_account_id,
                    "the analytic account is not propagated")
