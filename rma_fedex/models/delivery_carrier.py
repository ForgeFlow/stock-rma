# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.delivery_fedex.models.delivery_fedex import _convert_curr_iso_fdx
from odoo.addons.delivery_fedex.models.fedex_request import FedexRequest

_logger = logging.getLogger(__name__)


class ProviderFedex(models.Model):
    _inherit = "delivery.carrier"

    def fedex_get_return_label(self, picking, tracking_number=None, origin_date=None):
        srm = FedexRequest(
            self.log_xml,
            request_type="shipping",
            prod_environment=self.prod_environment,
        )
        superself = self.sudo()
        srm.web_authentication_detail(
            superself.fedex_developer_key, superself.fedex_developer_password
        )
        srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

        srm.transaction_detail(picking.id)

        package_type = (
            picking.package_ids
            and picking.package_ids[0].packaging_id.shipper_package_code
            or self.fedex_default_packaging_id.shipper_package_code
        )
        srm.shipment_request(
            self.fedex_droppoff_type,
            self.fedex_service_type,
            package_type,
            self.fedex_weight_unit,
            self.fedex_saturday_delivery,
        )
        srm.set_currency(_convert_curr_iso_fdx(picking.company_id.currency_id.name))
        srm.set_shipper(picking.partner_id, picking.partner_id)
        srm.set_recipient(picking.company_id.partner_id)

        srm.shipping_charges_payment(superself.fedex_account_number)

        srm.shipment_label(
            "COMMON2D",
            self.fedex_label_file_type,
            self.fedex_label_stock_type,
            "TOP_EDGE_OF_TEXT_FIRST",
            "SHIPPING_LABEL_FIRST",
        )
        # Need to discuss about our picking consider as a return picking or new picking
        # if we consider a new picking, need to discuss with Max
        # if picking.is_return_picking:
        net_weight = self._fedex_convert_weight(
            picking._get_estimated_weight(), self.fedex_weight_unit
        )
        # else:
        #     net_weight = self._fedex_convert_weight(
        #         picking.shipping_weight, self.fedex_weight_unit)
        packaging = packaging = (
            picking.package_ids[:1].packaging_id
            or picking.carrier_id.fedex_default_packaging_id
        )
        order = picking.sale_id
        po_number = order.display_name or False
        dept_number = False
        srm._add_package(
            net_weight,
            package_code=packaging.shipper_package_code,
            package_height=packaging.height,
            package_width=packaging.width,
            package_length=packaging.packaging_length,
            reference=picking.display_name,
            po_number=po_number,
            dept_number=dept_number,
        )
        srm.set_master_package(net_weight, 1)
        if self.fedex_service_type in [
            "INTERNATIONAL_ECONOMY",
            "INTERNATIONAL_PRIORITY",
        ] or (
            picking.partner_id.country_id.code == "IN"
            and picking.picking_type_id.warehouse_id.partner_id.country_id.code == "IN"
        ):

            order_currency = (
                picking.sale_id.currency_id or picking.company_id.currency_id
            )
            commodity_currency = order_currency
            total_commodities_amount = 0.0
            commodity_country_of_manufacture = (
                picking.picking_type_id.warehouse_id.partner_id.country_id.code
            )

            for operation in picking.move_line_ids:
                commodity_amount = (
                    operation.move_id.sale_line_id.price_unit
                    or operation.product_id.list_price
                )
                total_commodities_amount += commodity_amount * operation.qty_done
                commodity_description = operation.product_id.name
                commodity_number_of_piece = "1"
                commodity_weight_units = self.fedex_weight_unit
                if operation.state == "done":
                    commodity_weight_value = self._fedex_convert_weight(
                        operation.product_id.weight * operation.qty_done,
                        self.fedex_weight_unit,
                    )
                    commodity_quantity = operation.qty_done
                else:
                    commodity_weight_value = self._fedex_convert_weight(
                        operation.product_id.weight * operation.product_uom_qty,
                        self.fedex_weight_unit,
                    )
                    commodity_quantity = operation.product_uom_qty
                commodity_quantity_units = "EA"
                commodity_harmonized_code = operation.product_id.hs_code or ""
                srm.commodities(
                    _convert_curr_iso_fdx(commodity_currency.name),
                    commodity_amount,
                    commodity_number_of_piece,
                    commodity_weight_units,
                    commodity_weight_value,
                    commodity_description,
                    commodity_country_of_manufacture,
                    commodity_quantity,
                    commodity_quantity_units,
                    commodity_harmonized_code,
                )
            srm.customs_value(
                _convert_curr_iso_fdx(commodity_currency.name),
                total_commodities_amount,
                "NON_DOCUMENTS",
            )
            # We consider that returns are always paid by the company creating the label
            srm.duties_payment(
                picking.picking_type_id.warehouse_id.partner_id,
                superself.fedex_account_number,
                "SENDER",
            )
        srm.return_label(tracking_number, origin_date)
        response = srm.process_shipment()
        if not response.get("errors_message"):
            fedex_labels = [
                (
                    "%s-%s-%s.%s"
                    % (
                        self.get_return_label_prefix(),
                        response["tracking_number"],
                        index,
                        self.fedex_label_file_type,
                    ),
                    label,
                )
                for index, label in enumerate(
                    srm._get_labels(self.fedex_label_file_type)
                )
            ]

            picking.message_post(body=_("Return Label"), attachments=fedex_labels)
            rma_order_line_id = self.env["rma.order.line"].search(
                [("name", "=", picking.origin)]
            )
            if rma_order_line_id and rma_order_line_id.rma_id:
                rma_order_line_id.rma_id.message_post(
                    body=_("Return Label"), attachments=fedex_labels
                )
            return response, fedex_labels
        else:
            raise UserError(response["errors_message"])
