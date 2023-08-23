# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import Form, TransactionCase


class TestRmaMrp(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product_model = self.env["product.product"]
        self.template_model = self.env["product.template"]
        self.product_ctg_model = self.env["product.category"]
        self.journal_model = self.env["account.journal"]
        self.rma_line = self.env["rma.order.line"]
        self.rma_make_picking = self.env["rma_make_picking.wizard"]
        self.rma_op_obj = self.env["rma.operation"]
        # Get required Model data
        self.product_uom = self.env.ref("uom.product_uom_unit")
        self.company = self.env.ref("base.main_company")
        self.stock_picking_type_out = self.env.ref("stock.picking_type_out")
        self.stock_picking_type_in = self.env.ref("stock.picking_type_in")
        self.stock_location_id = self.env.ref("stock.stock_location_stock")
        self.stock_location_customer_id = self.env.ref("stock.stock_location_customers")
        self.stock_location_supplier_id = self.env.ref("stock.stock_location_suppliers")
        self.rma_route_cust = self.env.ref("rma.route_rma_customer")
        self.customer_view = self.env.ref("rma_sale.view_rma_line_form")

        self.stock_journal = self.env["account.journal"].create(
            {"name": "Stock journal", "type": "general", "code": "STK00"}
        )
        # Create product category
        self.product_ctg = self._create_product_category()

        # Create partners
        self.supplier = self.env["res.partner"].create({"name": "Test supplier"})
        self.customer = self.env["res.partner"].create({"name": "Test customer"})

        # Create a Product with real cost
        standard_price = 10.0
        list_price = 20.0
        self.kit_product = self._create_product(standard_price, False, list_price)
        self.component_product_1 = self._create_product(
            standard_price, False, list_price
        )
        self.component_product_2 = self._create_product(
            standard_price, False, list_price
        )

        # Create BoM for Kit A
        bom_product_form = Form(self.env["mrp.bom"])
        bom_product_form.product_id = self.kit_product
        bom_product_form.product_tmpl_id = self.kit_product.product_tmpl_id
        bom_product_form.product_qty = 1.0
        bom_product_form.type = "phantom"
        with bom_product_form.bom_line_ids.new() as bom_line:
            bom_line.product_id = self.component_product_1
            bom_line.product_qty = 1.0
        with bom_product_form.bom_line_ids.new() as bom_line:
            bom_line.product_id = self.component_product_2
            bom_line.product_qty = 1.0
        self.bom_kit = bom_product_form.save()

        # RMA configuration

        self.operation_1 = self.rma_op_obj.create(
            {
                "code": "TEST",
                "name": "Refund and receive",
                "type": "customer",
                "receipt_policy": "ordered",
                "refund_policy": "ordered",
                "in_route_id": self.rma_route_cust.id,
                "out_route_id": self.rma_route_cust.id,
            }
        )

    def _create_product_category(self):
        product_ctg = self.product_ctg_model.create(
            {
                "name": "test_product_ctg",
                "property_valuation": "real_time",
                "property_cost_method": "fifo",
                "property_stock_journal": self.stock_journal.id,
            }
        )
        return product_ctg

    def _create_product(self, standard_price, template, list_price):
        """Create a Product variant."""
        if not template:
            template = self.template_model.create(
                {
                    "name": "test_product",
                    "categ_id": self.product_ctg.id,
                    "type": "product",
                    "standard_price": standard_price,
                    "valuation": "real_time",
                    "invoice_policy": "delivery",
                }
            )
            return template.product_variant_ids[0]
        product = self.product_model.create(
            {"product_tmpl_id": template.id, "list_price": list_price}
        )
        return product

    def _create_receipt(self, product, qty, price_unit=10.0):
        return self.env["stock.picking"].create(
            {
                "name": self.stock_picking_type_in.sequence_id._next(),
                "partner_id": self.supplier.id,
                "picking_type_id": self.stock_picking_type_in.id,
                "location_id": self.stock_location_supplier_id.id,
                "location_dest_id": self.stock_location_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_uom": product.uom_id.id,
                            "product_uom_qty": qty,
                            "price_unit": price_unit,
                            "location_id": self.stock_location_supplier_id.id,
                            "location_dest_id": self.stock_location_id.id,
                            "procure_method": "make_to_stock",
                        },
                    )
                ],
            }
        )

    def _do_picking(self, picking, qty):
        """Do picking with only one move on the given date."""
        picking.action_confirm()
        picking.action_assign()
        picking.move_ids.quantity_done = qty
        res = picking.button_validate()
        if isinstance(res, dict) and res:
            backorder_wiz_id = res["res_id"]
            backorder_wiz = self.env["stock.backorder.confirmation"].browse(
                [backorder_wiz_id]
            )
            backorder_wiz.process()
        return True

    def _make_sale_order(self, product, quantity, price_unit=10.0):
        so = Form(self.env["sale.order"])
        so.partner_id = self.customer
        with so.order_line.new() as sale_line:
            sale_line.product_id = product
            sale_line.product_uom_qty = quantity
            sale_line.price_unit = price_unit or product.list_price
        so = so.save()
        so.action_confirm()
        return so

    def _receive_rma(self, rma_line_ids):
        wizard = self.rma_make_picking.with_context(
            active_ids=rma_line_ids.ids,
            active_model="rma.order.line",
            picking_type="incoming",
            active_id=1,
        ).create({})
        wizard._create_picking()
        pickings = rma_line_ids._get_in_pickings()
        pickings.action_assign()
        for picking in pickings:
            for mv in picking.move_ids:
                mv.quantity_done = mv.product_uom_qty
        # In case of two step pickings, ship in two steps:
        while pickings.filtered(lambda p: p.state == "assigned"):
            pickings._action_done()
        return pickings

    def _create_rma_receipt(self, so_line, price_unit=10.0):
        rma_line = Form(
            self.rma_line.with_context(customer=1),
            view=self.customer_view.id,
        )
        rma_line.partner_id = so_line.order_id.partner_id
        rma_line.sale_line_id = so_line
        rma_line.price_unit = price_unit
        rma_line.operation_id = self.operation_1
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        picking = self._receive_rma(rma_line)
        return picking

    def test_01_kit_return_with_diff_prices(self):
        receipt_01 = self._create_receipt(self.component_product_1, 10, 10.0)
        self._do_picking(receipt_01, 10.0)
        receipt_02 = self._create_receipt(self.component_product_2, 10, 10.0)
        self._do_picking(receipt_02, 10.0)

        order_01 = self._make_sale_order(self.kit_product, 10, 30.0)
        self._do_picking(order_01.picking_ids, 10.0)

        receipt_03 = self._create_receipt(self.component_product_1, 10, 15.0)
        self._do_picking(receipt_03, 10.0)
        receipt_04 = self._create_receipt(self.component_product_2, 10, 15.0)
        self._do_picking(receipt_04, 10.0)

        order_02 = self._make_sale_order(self.kit_product, 10, 30.0)
        self._do_picking(order_02.picking_ids, 10.0)

        rma_picking_01 = self._create_rma_receipt(
            order_01.order_line, order_01.order_line.price_unit
        )

        component_1_sm = rma_picking_01.move_ids.filtered(
            lambda x: x.product_id == self.component_product_1
        )
        component_2_sm = rma_picking_01.move_ids.filtered(
            lambda x: x.product_id == self.component_product_2
        )

        self.assertTrue(bool(component_1_sm))
        self.assertTrue(bool(component_2_sm))

        self.component_product_1.standard_price = 20.0
        self.component_product_2.standard_price = 20.0

        self.assertEqual(
            100.0, sum(component_1_sm.mapped("stock_valuation_layer_ids.value"))
        )
        self.assertEqual(
            100.0, sum(component_2_sm.mapped("stock_valuation_layer_ids.value"))
        )

        rma_picking_02 = self._create_rma_receipt(
            order_02.order_line, order_02.order_line.price_unit
        )

        component_1_sm = rma_picking_02.move_ids.filtered(
            lambda x: x.product_id == self.component_product_1
        )
        component_2_sm = rma_picking_02.move_ids.filtered(
            lambda x: x.product_id == self.component_product_2
        )

        self.assertTrue(bool(component_1_sm))
        self.assertTrue(bool(component_2_sm))

        self.component_product_1.standard_price = 25.0
        self.component_product_2.standard_price = 25.0

        self.assertEqual(
            150.0, sum(component_1_sm.mapped("stock_valuation_layer_ids.value"))
        )
        self.assertEqual(
            150.0, sum(component_2_sm.mapped("stock_valuation_layer_ids.value"))
        )
