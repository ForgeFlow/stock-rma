# Copyright 2024 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo.addons.stock.models.stock_picking import Picking


# flake8: noqa: C901
def post_load_hook():
    def _check_entire_pack(self):
        """This function check if entire packs are moved in the picking"""
        for picking in self:
            origin_packages = picking.move_line_ids.mapped("package_id")
            for pack in origin_packages:
                if picking._check_move_lines_map_quant_package(pack):
                    package_level_ids = picking.package_level_ids.filtered(
                        lambda pl: pl.package_id == pack
                    )
                    move_lines_to_pack = picking.move_line_ids.filtered(
                        lambda ml: ml.package_id == pack
                        and not ml.result_package_id
                        and ml.state not in ("done", "cancel")
                    )
                    if not package_level_ids:
                        package_location = (
                            self._get_entire_pack_location_dest(move_lines_to_pack)
                            or picking.location_dest_id.id
                        )
                        self.env["stock.package_level"].with_context(
                            bypass_reservation_update=package_location
                        ).create(
                            {
                                "picking_id": picking.id,
                                "package_id": pack.id,
                                "location_id": pack.location_id.id,
                                "location_dest_id": package_location,
                                "move_line_ids": [(6, 0, move_lines_to_pack.ids)],
                                "company_id": picking.company_id.id,
                            }
                        )
                        # Propagate the result package in the next move for disposable packages only.
                        # Start Hook
                        if (
                            pack.package_use == "disposable"
                            and pack.location_id.usage != "customer"
                        ):
                            # End Hook
                            move_lines_to_pack.with_context(
                                bypass_reservation_update=package_location
                            ).write({"result_package_id": pack.id})

                    else:
                        move_lines_in_package_level = move_lines_to_pack.filtered(
                            lambda ml: ml.move_id.package_level_id
                        )
                        move_lines_without_package_level = (
                            move_lines_to_pack - move_lines_in_package_level
                        )

                        if pack.package_use == "disposable":
                            (
                                move_lines_in_package_level
                                | move_lines_without_package_level
                            ).result_package_id = pack
                        move_lines_in_package_level.result_package_id = pack
                        for ml in move_lines_in_package_level:
                            ml.package_level_id = ml.move_id.package_level_id.id

                        move_lines_without_package_level.package_level_id = (
                            package_level_ids[0]
                        )
                        for pl in package_level_ids:
                            pl.location_dest_id = (
                                self._get_entire_pack_location_dest(pl.move_line_ids)
                                or picking.location_dest_id.id
                            )

    if not hasattr(Picking, "_check_entire_pack_original"):
        Picking._check_entire_pack_original = Picking._check_entire_pack
    Picking._check_entire_pack = _check_entire_pack
