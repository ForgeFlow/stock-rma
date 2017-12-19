# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.addons.rma.tests import test_rma


class TestSupplierRma(test_rma.TestRma):

    def setUp(self):
        super(TestSupplierRma, self).setUp()
        products2move = [(self.product_1, 3), (self.product_2, 5),
                         (self.product_3, 2)]
        self.rma_supplier_id = self._create_rma_from_move(
            products2move, 'supplier', self.env.ref('base.res_partner_1'),
            dropship=False)

    def test_supplier_rma(self):
        wizard = self.rma_make_picking.with_context({
            'active_ids': self.rma_supplier_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'outgoing',
            'active_id': 1
        }).create({})
        procurements = wizard._create_picking()
        group_ids = set([proc.group_id.id for proc in procurements if
                         proc.group_id])
        domain = [('group_id', 'in', list(group_ids))]
        picking = self.stockpicking.search(domain)
        self.assertEquals(len(picking), 1,
                          "Incorrect number of pickings created")
        moves = picking.move_lines
        self.assertEquals(len(moves), 3,
                          "Incorrect number of moves created")
        for line in self.rma_supplier_id.rma_line_ids:
            # common qtys for all products
            self.assertEquals(line.qty_received, 0,
                              "Wrong qty received")
            self.assertEquals(line.qty_incoming, 0,
                              "Wrong qty incoming")
            self.assertEquals(line.qty_delivered, 0,
                              "Wrong qty delivered")
            # product specific
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_to_receive, 3,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_to_deliver, 3,
                                  "Wrong qty to deliver")
                self.assertEquals(line.qty_outgoing, 3,
                                  "Wrong qty outgoing")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_to_receive, 5,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_to_deliver, 5,
                                  "Wrong qty to deliver")
                self.assertEquals(line.qty_outgoing, 5,
                                  "Wrong qty outgoing")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_to_receive, 2,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_to_deliver, 2,
                                  "Wrong qty to deliver")
                self.assertEquals(line.qty_outgoing, 2,
                                  "Wrong qty outgoing")

        picking.action_assign()
        picking.do_transfer()
        for line in self.rma_supplier_id.rma_line_ids:
            self.assertEquals(line.qty_to_deliver, 0,
                              "Wrong qty to deliver")
            self.assertEquals(line.qty_incoming, 0,
                              "Wrong qty incoming")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            self.assertEquals(line.qty_received, 0,
                              "Wrong qty received")
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_delivered, 3,
                                  "Wrong qty delivered")
                self.assertEquals(line.qty_to_receive, 3,
                                  "Wrong qty to receive")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_delivered, 5,
                                  "Wrong qty delivered")
                self.assertEquals(line.qty_to_receive, 5,
                                  "Wrong qty to receive")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_delivered, 2,
                                  "Wrong qty delivered")
                self.assertEquals(line.qty_to_receive, 2,
                                  "Wrong qty to receive")
        wizard = self.rma_make_picking.with_context({
            'active_id': 1,
            'active_ids': self.rma_supplier_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'incoming',
        }).create({})
        procurements = wizard._create_picking()
        group_ids = set([proc.group_id.id for proc in procurements if
                         proc.group_id])
        domain = [('group_id', 'in', list(group_ids))]
        pickings = self.stockpicking.search(domain)
        self.assertEquals(len(pickings), 2,
                          "Incorrect number of pickings created")
        picking_out = pickings[1]
        moves = picking_out.move_lines
        self.assertEquals(len(moves), 3,
                          "Incorrect number of moves created")
        for line in self.rma_supplier_id.rma_line_ids:
            self.assertEquals(line.qty_to_deliver, 0,
                              "Wrong qty to deliver")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            self.assertEquals(line.qty_received, 0,
                              "Wrong qty received")
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_to_receive, 3,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_incoming, 3,
                                  "Wrong qty incoming")
                self.assertEquals(line.qty_delivered, 3,
                                  "Wrong qty delivered")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_to_receive, 5,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_incoming, 5,
                                  "Wrong qty incoming")
                self.assertEquals(line.qty_delivered, 5,
                                  "Wrong qty delivered")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_to_receive, 2,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_incoming, 2,
                                  "Wrong qty incoming")
                self.assertEquals(line.qty_delivered, 2,
                                  "Wrong qty delivered")
        picking_out.action_assign()
        picking_out.do_transfer()
        for line in self.rma_supplier_id.rma_line_ids:
            self.assertEquals(line.qty_to_receive, 0,
                              "Wrong qty to receive")
            self.assertEquals(line.qty_incoming, 0,
                              "Wrong qty incoming")
            self.assertEquals(line.qty_to_deliver, 0,
                              "Wrong qty to deliver")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_received, 3,
                                  "Wrong qty received")
                self.assertEquals(line.qty_delivered, 3,
                                  "Wrong qty delivered")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_received, 5,
                                  "Wrong qty received")
                self.assertEquals(line.qty_delivered, 5,
                                  "Wrong qty delivered")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_received, 2,
                                  "Wrong qty received")
                self.assertEquals(line.qty_delivered, 2,
                                  "Wrong qty delivered")
        self.rma_supplier_id.action_rma_done()
        self.assertEquals(self.rma_supplier_id.state, 'done',
                          "Wrong State")
