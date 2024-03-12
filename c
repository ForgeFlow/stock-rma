[33mcommit 46fa1f62830afde22dd76d6830f69a698264ead2[m[33m ([m[1;36mHEAD -> [m[1;32m17.0-mig-rma[m[33m)[m
Author: Carlos Vallés Fuster <carlos.valles@forgeflow.com>
Date:   Wed Mar 6 08:32:41 2024 +0100

    [IMP] rma: pre-commit auto fixes

[33mcommit f4577808ab2d11930a5eb31ed2e2427ac229eb84[m
Author: Florian da Costa <florian.dacosta@akretion.com>
Date:   Tue Nov 28 12:56:20 2023 +0100

    [IMP] Remove domain from onchange method and put it in field view

[33mcommit b9f0b7a60df38a05a8bbce4d6be147cab52ff3ac[m
Author: Florian da Costa <florian.dacosta@akretion.com>
Date:   Tue Nov 28 09:52:38 2023 +0100

    [FIX] Delete rma_picking_wizard_item on cascade to avoid failure

[33mcommit 338c2f83694766104d428758aa141abdb67e0295[m
Author: JordiMForgeFlow <jordi.masvidal@forgeflow.com>
Date:   Mon Nov 20 10:12:41 2023 +0100

    [IMP] rma: mark RMA location as return location

[33mcommit 8df45b0fe2ebb6b3e7785db66407dcd4248812e2[m
Author: AaronHForgeFlow <aaron.henriquez@forgeflow.com>
Date:   Thu Nov 16 15:40:01 2023 +0100

    [FIX] rma: RMA location in the warehouse should not be inside stock

[33mcommit 8e5b21126b05cfb9a823e974099201c7007dabe7[m
Author: ChrisOForgeFlow <94866688+ChrisOForgeFlow@users.noreply.github.com>
Date:   Fri Oct 27 07:41:54 2023 -0500

    [14.0][IMP] added default operation on rma group, easy setup before rma lines created (#452)

    * [14.0][IMP] added default operation on rma group, easy setup before rma lines created

    * [IMP] added fields for default route created by wizard on rma group

    * fix: get right price after create rma order line

[33mcommit 1d71d2862e036d3b0d737730fa108feeb1ee45ce[m
Author: SergiCForgeFlow <sergi.casau@forgeflow.com>
Date:   Tue Apr 4 11:45:50 2023 +0200

    [FIX] Restrict approval rights to RMA Manager

[33mcommit fe1bcddd748fb91d5fa3fe1785ad94f574808b52[m
Author: AaronHForgeFlow <aaron.henriquez@forgeflow.com>
Date:   Fri Oct 27 11:49:33 2023 +0200

    [IMP] rma: date_rma in lines

[33mcommit ee0d1fda11ef27a3d19c80a59c7a090091878387[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Fri Apr 28 10:37:41 2023 +0200

    [IMP] rma: add date to rma_order_line

[33mcommit 5ee74fda1363e9db5c3b3194d9414fc600952bb0[m
Author: Florian da Costa <florian.dacosta@akretion.com>
Date:   Fri Oct 27 09:35:40 2023 +0200

    rma : Fix description size in rma order line view form

[33mcommit 91fec438b97f176c624f6ef8b48d6222ac881243[m
Author: JordiMForgeFlow <jordi.masvidal@forgeflow.com>
Date:   Tue Oct 10 10:18:02 2023 +0200

    [FIX] rma: correctly display fields in product category view

[33mcommit 23da1ccb94dbd9603ccd8ba71e5efcb6b3eb55a2[m
Author: Joan Sisquella <joan.sisquella@forgeflow.com>
Date:   Thu May 25 17:53:49 2023 +0200

    [FIX] rma: procurement origin

    In the current implementation of Odoo's _assign_picking() method in stock.move, there's a conditional check that looks at whether all the moves associated with a picking have the same partner_id and origin. If any move doesn't align with these conditions, the origin of the picking is set to False.

            if any(picking.partner_id.id != m.partner_id.id or
                    picking.origin != m.origin for m in moves):
                # If a picking is found, we'll append `move` to its move list and thus its
                # `partner_id` and `ref` field will refer to multiple records. In this
                # case, we chose to  wipe them.
                picking.write({
                    'partner_id': False,
                    'origin': False,
                })
    In the context of RMA when we have multiple moves associated with a picking, each coming from a different RMA order line, we encounter a problem. Each move has its origin set as the name of the RMA orde line (line.name), so as soon as a second move from a different line is appended to the picking, the origin of the picking is wiped, because it doesn't match the origin of the first move.

    In order to prevent the partner_id of the picking from being set to False when there are multiple associated moves, I propose that we change the origin of the procurement from the name of the RMA line to the name of the procurement group (group.name). This way, all moves associated with a picking will share the same origin, preserving the origin of the picking and ensuring it doesn't get inadvertently set to False.

[33mcommit eee6edcc2f4e4cd641ea480f3c4f53b950218721[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Tue May 2 10:17:08 2023 +0200

    [FIX] rma: get_move_rma dropship

[33mcommit 0fa5fa17b01b695f660e3298b8269dcd351dd69d[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Tue May 2 09:34:46 2023 +0200

    [FIX] rma: dropship from vendor as outgoing

[33mcommit a2e03f1c26adf6a88e2a08df80295757d48ce928[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Tue May 2 09:32:46 2023 +0200

    [FIX] rma: get all partner RMA

[33mcommit 92c591f3308911fe0d87094b8b8dfeb85af550b8[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Thu Mar 9 19:57:20 2023 +0100

    [FIX] rma: some fixups

[33mcommit 010bdc507063b790e9304a2c4d004e13de9021b5[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Thu Mar 9 18:19:17 2023 +0100

    [FIX] rma: make picking product_uom_qty

[33mcommit 0422852a8848b2b68ddae15f4117d012af837c61[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Fri Mar 3 17:00:11 2023 +0100

    [FIX] rma: product_uom_qty not in move_line_ids

[33mcommit b67ac1748c5a99434891170504d1091cbce92b02[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Wed Feb 22 15:33:49 2023 +0100

    [16.0][FIX] rma: return of button done

[33mcommit 87214a6c220610e060c3c94af507d71558ebf8e4[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Wed Feb 22 15:25:47 2023 +0100

    [FIX] rma: deprecated test warning fix

[33mcommit 391aaa8f934deaff0f52e5d14ec0e1c71286a803[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Tue Feb 21 15:03:29 2023 +0100

    [IMP] rma: limit state statusbar

[33mcommit 2a5952e147e621a180f99599332d2f0331bd6a2b[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Tue Feb 21 11:31:47 2023 +0100

    [FIX] rma: in multi step routes, only reserve first step

    We shoul not force reservation on next steps on a multi step
    route, oherwise a inconsistency is generated and the transfers
    cannot be processed or cancel so the user gets stuck ("it is
    not possible to unreserve more products that you have in stock"
    error).

[33mcommit 4dabdbac2c34858cbeacdfe04108bec1b7dfba4e[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Tue Feb 14 17:31:07 2023 +0100

    [IMP] rma: cancel rma_lines

[33mcommit 2989ff7bf6448008c6990026562ca45d1c8209ee[m
Author: Florian da Costa <florian.dacosta@akretion.com>
Date:   Thu Dec 1 17:23:25 2022 +0100

    [FIX] Move some field from onchange to compute fields to avoid issues in views

[33mcommit 8f31e4534fd4b9b0ce044cd3bf1b46f3d74e9d72[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Wed Feb 1 12:57:03 2023 +0100

    [14.0][FIX] rma: add stock move in supplier group

[33mcommit 6ca45d19a2ec70c0c73174fddca54a787afa0312[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Thu Jan 5 15:44:04 2023 +0100

    [FIX] rma: remove "Add new line" in RMA group.

    This was not the intended way to add RMA lines to a group.
    Users are supposed to use the wizards to do so (add from stock
    move, add from serial, etc.). Having the option to use "add
    new line" was only leading to errors and confusion.

[33mcommit c2698b2d5e8efa114eaac911d7ac3bf03f7969db[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Mon Jan 2 11:10:02 2023 +0100

    [IMP] rma: print serial/lot number in RMA group report

[33mcommit 258118b556a5ca48910216677471df89d0697904[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Mon Jan 2 10:56:18 2023 +0100

    [IMP] rma: order by id desc

[33mcommit e0cb763b87c043a7e02d43c2d890d256762bea05[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Mon Jan 2 10:54:00 2023 +0100

    [IMP] rma: add description to rma order and copy it over to new lines

[33mcommit faaf848fd56a6b87c603d433c3049b2bb7cc7b69[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Mon Jan 2 10:22:03 2023 +0100

    [IMP] rma: rma group supplier form view as a inherited view.

    The goal is to simplify view defintion and do not duplicate
    things, requiring to do view changes in two places.

    The same change was done from rma lines some time ago.

[33mcommit 5042966fd83893fd4b6cac667463c6d17ee9a1d3[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Wed Dec 28 13:11:19 2022 +0100

    [FIX] rma: Ensure that configuration on the operation is applied

    Without this, some policies are not being copied from the
    operation selected when creating new rma line from a rma group.

    In v16 this patch and the usage of such onchange can be removed
    in favor of (pre)computed stored editable fields for all policies
    and configuration in the RMA operation.

[33mcommit b323c50d0ff8d4b80c4c66f20b58411d35476c93[m
Author: Florian da Costa <florian.dacosta@akretion.com>
Date:   Tue May 3 10:46:14 2022 +0200

    [FIX] count produced products going to customer as out pickings

[33mcommit bd42a48711ca301cd2702946f486f432d631c2e4[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Tue Dec 20 10:16:01 2022 +0100

    [14.0][IMP] rma: add lot/serial in report

[33mcommit ee4b9601f3daadd7df6b3b6b21f7de0dcaa4a0bb[m
Author: AnnaPForgeFlow <anna.puig@forgeflow.com>
Date:   Mon Nov 7 10:22:51 2022 +0100

    [IMP] rma: add translations

[33mcommit 2ce1b6d4b21239cea3e99dfd1472b7f63cb4eccd[m
Author: Jordi Ballester Alomar <jordi.ballester@forgeflow.com>
Date:   Wed Nov 30 16:34:44 2022 +0100

    [FIX] fix empty parter on rma picking

[33mcommit c4f6100703541ac05cd7622835be47e0e2f554e2[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Wed Nov 30 12:58:14 2022 +0100

    [14.0][IMP] rma: pass product in create lot

[33mcommit 0bb07d5e0199d8590b501be3cec75dd39541f962[m
Author: Florian da Costa <florian.dacosta@akretion.com>
Date:   Mon Nov 28 15:07:46 2022 +0100

    [16.0][MIG] Migrate rma module to v16

[33mcommit 1a2599e86602b04304616c16a9b187ac340cf8a5[m
Author: Jordi Ballester Alomar <jordi.ballester@forgeflow.com>
Date:   Wed Nov 23 15:26:03 2022 +0100

    [IMP] centralize the logic to get the correct cost of the RMA.

[33mcommit 4f59aea9e33a1d4865dc81ff1db71e31d4afadc8[m
Author: Jordi Ballester Alomar <jordi.ballester@forgeflow.com>
Date:   Mon Nov 21 15:13:06 2022 +0100

    [FIX] include anglo-saxon price unit calculation in refunds.
    Otherwise the anglo saxon entries won't be correct.
    For example, the Interim (Delivered) account should balance
    after receiving and triggering a refund on a customer rma.

[33mcommit b688c7faae6ab6e6ed4a699e864ffaf415444e58[m
Author: Jordi Ballester <jordi.ballester@forgeflow.com>
Date:   Sun Jun 26 08:38:43 2022 +0200

    [IMP] rma_sale: introduce new config settings.
    - auto_confirm_rma_sale
    - free_of_charge_rma_sale

[33mcommit d91868ff4dc948a1bb6b78466b3943eefce465e2[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Mon Jul 11 10:17:38 2022 +0200

    [15.0][FIX] rma_sale: fixup of procurement

[33mcommit 84ee05edcc364073b7bdf30edc4045a9ce2c1d5f[m
Author: Stefan Rijnhart <stefan@opener.am>
Date:   Sat Jun 11 12:09:06 2022 +0200

    [IMP] rma: prevent the creation of zero qty moves

[33mcommit 84cec307495f82218e116c88af2ec1b7c7c9cffa[m
Author: Florian da Costa <florian.dacosta@akretion.com>
Date:   Fri Jul 1 13:53:14 2022 +0200

    [IMP] Make rma order view cleaner for user
    Hide button and fields depending on the policy chosen on the rma line

[33mcommit fc1cde633612da0c25d8bd12ede08d30b7e66d8e[m
Author: Florian da Costa <florian.dacosta@akretion.com>
Date:   Wed Jun 8 15:55:52 2022 +0200

    Hide smart button when empty

[33mcommit b96eff7aac05c39691526333a2ff3748c022834d[m
Author: Stefan Rijnhart <stefan@opener.am>
Date:   Fri Jun 24 12:07:31 2022 +0200

    [FIX] rma: improve check on rule selection during procurement

    Fixes #274

    Thanks to @florian-dacosta for suggesting this approach.

[33mcommit d3da7fe3cc1becd780fc7b3d3cad9a7a965631db[m
Author: DavidJForgeFlow <david.jimenez@forgeflow.com>
Date:   Thu Jun 16 11:53:30 2022 +0200

    [FIX]rma: remove test_rma dependency to Account

[33mcommit 5ac2ad5e3cd105cae266d22606be86db2bac29fe[m
Author: Cas Vissers <c.vissers@brahoo.nl>
Date:   Thu Jun 16 09:30:13 2022 +0200

    [IMP] Improve multi-company record rules

[33mcommit 5abc94ae3c74ace28ea3d2de5dc2110e2a554d4f[m
Author: Stefan Rijnhart <stefan@opener.am>
Date:   Wed Jun 15 17:35:17 2022 +0200

    [FIX] rma: prevent against warehouse mismatch or missing rules

    When creating pickings, ensure that the applied stock rule was taken from
    the operation's routes. Otherwise, the default procurement rules for a
    warehouse may kick in, creating incoming customer goods not from the customer
    location but from the resupply warehouse.

[33mcommit b8816135e8ba9b37a5ae8409e645e40e9bcacbd5[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Mon May 23 18:39:20 2022 +0200

    [IMP] rma: add rma lines to group selecting serial numbers

[33mcommit c8f6549604f84cad7e055f513ffabddb40435b3e[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Fri May 13 15:15:36 2022 +0200

    [IMP] rma: add RMA reference to delivery slip report

[33mcommit ba37754303d5de093ea39f70791267d22ba9b4d6[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Wed May 25 17:57:40 2022 +0200

    [FIX] rma:  missing migration scripts and version bump

    Those are needed after making some fields company dependent

[33mcommit 7f989dccf5bc0f80166307034aae05fe77450c1f[m
Author: DavidFIB <david.jimenez.gomariz@estudiantat.upc.edu>
Date:   Thu May 19 14:03:40 2022 +0200

    [15.0][FIX/IMP] Make RMA Operation settings company dependent

[33mcommit c1052effb9304a3540acd994bcb474884bf67384[m
Author: DavidFIB <david.jimenez.gomariz@estudiantat.upc.edu>
Date:   Wed May 18 17:11:45 2022 +0200

    [14.0][FIX/IMP] Make RMA Operation settings company dependent

[33mcommit 80ea8e3c24d4c1731af551d220e6c4762a20591c[m
Author: Andrea <a.stirpe@onestein.nl>
Date:   Wed Apr 20 16:34:53 2022 +0200

    [13.0][FIX/IMP] Make RMA Operation settings company dependent

[33mcommit 55fdf4508a5992b2415650e3a101ff2af15eb17e[m
Author: AaronHForgeFlow <ahenriquez@eficent.com>
Date:   Fri Mar 4 10:56:07 2022 +0100

    [15.0][IMP] Tests for stock valuation
    [FIX] rma: rma_custmer_user has no write permissions in partner, so compute method fails.
    [IMP] rma: use rma user in tests
    [FIX] rma_account: move_line_id field string
    [IMP] rma, rma_account, rma_sale, rma_purchase: tests for stock valuation
    [FIX] account_move_line_rma_order_line: minor lint, make auto-install

[33mcommit 8bedb814cfa2030cfe1946ff108270c0afcfa2b3[m
Author: Jordi Ballester <jordi.ballester@forgeflow.com>
Date:   Wed Mar 2 11:35:08 2022 +0100

    [IMP] rma: Refactor all rma modules in order to consider using the correct price unit in moves
    Otherwise the inventory accounting will be completely wrong.

[33mcommit d6960ba8b7a1103adb1c5cbb16ba8fec4b082b2a[m
Author: Florian da Costa <florian.dacosta@akretion.com>
Date:   Fri Apr 29 15:54:28 2022 +0200

    Add missing fields in rma line editable tree in rma group

[33mcommit 37ec3958c811986deec7d088497405d3cb0ca53a[m
Author: Florian da Costa <florian.dacosta@akretion.com>
Date:   Tue May 3 10:06:43 2022 +0200

    [FIX] Remove useless/bad wiz_id field in rma_make_picking.wizard item preparation

[33mcommit 329887509c1c0fc34dfe6cbceeb4ff6e4232c6da[m
Author: AaronHForgeFlow <ahenriquez@eficent.com>
Date:   Fri Apr 22 12:00:44 2022 +0200

    [IMP] COPIER UPDATE: black, isort, prettier

[33mcommit 8a0661b4eb8752f31db6ab8644ec25c638d8c3e6[m
Author: Christopher Ormaza <chris.ormaza@forgeflow.com>
Date:   Thu Mar 3 11:53:14 2022 -0500

    [14.0][FIX] rma: separate stock.move by rma_line_id to fix picking association

[33mcommit a15d7b92660c1e56ef3c3b0df796a5cf2d9a69b0[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Fri Mar 4 12:01:02 2022 +0100

    [FIX] rma: do not force reservation on supplier RMA deliveries

    * remove code call to unexisting `force_asign`.
    * only one model per model file and rename as appropriate.

[33mcommit c820fb00fdafe61d32925eac58a1ebad3c631545[m
Author: Jasmin Solanki <jasmin.solanki@forgeflow.com>
Date:   Wed Feb 23 10:19:21 2022 +0530

    [IMP] rma: Fix Route View

[33mcommit b9d6f0d2f81831adf2056da999ad079ac5ba1fce[m
Author: Christopher Ormaza <chris.ormaza@forgeflow.com>
Date:   Fri Feb 11 11:25:20 2022 -0500

    [15.0][ADD] Mass action for request approval RMA order line

[33mcommit 58c6f344dc565e7762fd850894fa054602d0eb64[m
Author: Christopher Ormaza <chris.ormaza@forgeflow.com>
Date:   Mon Feb 7 09:03:08 2022 -0500

    [FIX] rma: add lot to pickings created from wizard on RMA lines

[33mcommit c3834483839785ca29f36077b90df79da3757c4b[m
Author: Christopher Ormaza <chris.ormaza@forgeflow.com>
Date:   Fri Jan 28 11:23:47 2022 -0500

    [IMP] rma, rma_sale: added select all, messages for UX

[33mcommit e9757291b2147cce79c7939e0b1bc05a8235ce97[m
Author: Christopher Ormaza <chris.ormaza@forgeflow.com>
Date:   Tue Jan 25 11:26:23 2022 -0500

    [IMP] rma: Added serial/lot selection on from stock move wizard on rma groups
    - added restriction to approve rma with product tracking on serial, should be only one to receive

[33mcommit 3c8c4e92a0e03b8fc43b519cb7d39970fa15d834[m
Author: Jordi Ballester <jordi.ballester@forgeflow.com>
Date:   Mon Feb 7 09:16:32 2022 +0100

    [FIX] rma: compute out_shipment_count correctly. Add test cases

[33mcommit da1b81c29e1f78a80112713397ae25ddebc5e454[m
Author: Jordi Ballester <jordi.ballester@forgeflow.com>
Date:   Thu Feb 3 16:04:59 2022 +0100

    [fix] rma: improve logic to count in and out pickings
    In the scenario where we use a 2 or 3 step receipts or pickings
    we want to make sure that we correctly count and classify the pickings.

[33mcommit e2cc826381916c3794c63c9eec25f1365260d07c[m
Author: Jordi Ballester <jordi.ballester@forgeflow.com>
Date:   Wed Feb 2 22:53:30 2022 +0100

    [fix] rma: when using 2 step receipt or delivery, don't count double

[33mcommit 4de713d759021a5dd0cbc9ab56d980f272113762[m
Author: AaronHForgeFlow <ahenriquez@eficent.com>
Date:   Wed Jan 19 18:15:21 2022 +0100

    [14.0][IMP]rma: make operation editable after approved
    * remove also validation error when setting the rma to draft where there are done pickings

[33mcommit 79816ca9440beb84eb723ecc6016e614969b5452[m
Author: Jasmin Solanki <jasmin.solanki@forgeflow.com>
Date:   Fri Jan 7 16:37:52 2022 +0530

    [MIG] rma: Migration to 15.0

[33mcommit bfa70f0aba165cb113ac8bf068a230fce3f42dbc[m
Author: Jordi Ballester <jordi.ballester@forgeflow.com>
Date:   Wed Oct 27 18:58:41 2021 +0200

    [rma][fix] allow to set back to approved a done rma

[33mcommit e56b3f285393ecc292abe75a88c10546db9a6f29[m
Author: Mateu Griful <mateu.griful@forgeflow.com>
Date:   Wed Oct 6 12:27:46 2021 +0200

    Fix Pre-commit Websites

[33mcommit f714e722ee0cb205d9858467151030563b4d4b5f[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Fri Apr 16 13:07:38 2021 +0200

    [14.0][MIG] rma*: ir.actions.act_window has different access
    right in v14. Actions that read those records need to use
    `sudo` to allow non-admin users to be able to use these actions.

[33mcommit 735328d5bdea72e738c4580858c873127f048169[m
Author: Raphael Lee <51208020+RLeeOSI@users.noreply.github.com>
Date:   Wed Mar 17 14:45:57 2021 -0700

    [14.0][FIX] warehouse rma location

[33mcommit 80362935b91287a7e4e7491be5c293c6e7a0f6ce[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Fri Mar 26 11:27:15 2021 +0100

    [IMP] rma: Do not highlight all action buttons and simplify
    rma.line views, supplier view is an extension of customer one.

    This makes easier to edit common elements in both views and ease
    maintenance.

[33mcommit c34a26b7e9b7399bd4352175ebc92187fc3dabb5[m
Author: Lois Rilo <lois.rilo@forgeflow.com>
Date:   Fri Mar 26 09:53:18 2021 +0100

    [FIX] rma: toggle archive button removed in favor of web_ribbon.

[33mcommit 042a217c5760b92d1e35ba4d1491a2494162a852[m
Author: MateuGForgeFlow <mateu.griful@forgeflow.com>
Date:   Mon Feb 1 08:55:19 2021 +0100

    [14.0][IMP]Fill rma lines in tree (#156)

    * [IMP] rma: Fill rma lines in tree

[33mcommit 6b773e8e46ed3405c0332b93ee37c76934945afc[m
Author: Mateu Griful <mateu.griful@forgeflow.com>
Date:   Mon Jan 18 09:20:30 2021 +0100

    [MIG] rma_account: Migration to 14.0

[33mcommit d2abe224c4ac20d8064760067aa2dc510acc1d4c[m
Author: Mateu Griful <mateu.griful@forgeflow.com>
Date:   Fri Jan 15 16:43:42 2021 +0100

    [FIX] rma: Create rma supplier action

[33mcommit 424734f2e6b8a47419e90f6da99d319ed1b7e382[m
Author: Mateu Griful <mateu.griful@forgeflow.com>
Date:   Wed Jan 13 10:14:00 2021 +0100

    [MIG] rma: Migration to 14.0 - fix

[33mcommit 50c4f586c465f5aadfc98cf78a2192fdc7dafbeb[m
Author: Mateu Griful <mateu.griful@forgeflow.com>
Date:   Wed Jan 13 09:49:14 2021 +0100

    [MIG] rma: Migration to 14.0 - fix

[33mcommit 28fcd8efbe559ec2c72e9ead30af5ab985382d33[m
Author: Mateu Griful <mateu.griful@forgeflow.com>
Date:   Tue Jan 12 18:13:54 2021 +0100

    [MIG] rma: Migration to 14.0 - fix

[33mcommit 3efe41ed86df201764f565789efa9683e78c004f[m
Author: Mateu Griful <mateu.griful@forgeflow.com>
Date:   Tue Jan 12 16:54:43 2021 +0100

    [MIG] rma: Migration to 14.0 - fix

[33mcommit eee8207282f8bf282f5b6cc556bf2239c0934fd5[m
Author: Mateu Griful <mateu.griful@forgeflow.com>
Date:   Mon Dec 28 13:41:31 2020 +0100

    [IMP] rma
    Improve security

[33mcommit 5c61813584446ede8ed1e4a67cdb9bc432553466[m
Author: Mateu Griful <mateu.griful@forgeflow.com>
Date:   Fri Dec 18 15:35:40 2020 +0100

    [MIG] rma: Migration to 14.0

[33mcommit 682785c0cbe3c8cac690a9b891e68fb0c5abbdd4[m
Author: Mateu Griful <mateu.griful@forgeflow.com>
Date:   Fri Dec 18 12:26:29 2020 +0100

    [IMP] rma: black, isort, prettier

[33mcommit 81bd877890b59d195943220beca06d273895969c[m
Author: Bhavesh Odedra <bodedra@opensourceintegrators.com>
Date:   Wed Dec 16 19:34:18 2020 -0700

    [FIX] External ID not found in the system: account.res_partner_action_supplier

[33mcommit 072632af5f7ba0eefee0f1735985ed0e821badf3[m
Author: HviorForgeFlow <hector.villarreal@forgeflow.com>
Date:   Fri May 29 12:27:01 2020 +0200

    [IMP] Update pre-commit lints according with OCA ones

[33mcommit 942b50013e045b2fca4811de3d8df4aa6d517418[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Mon May 4 19:09:10 2020 +0200

    [FIX]rma report templates group

[33mcommit ff40a0c52fdb090368584eea556d381d468793da[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Thu Jan 23 11:37:38 2020 +0100

    [ENH]rma_sale traceability

[33mcommit 3d974ca2884d4f826217e494cb08d24617c5f737[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Fri Feb 14 13:14:45 2020 +0100

    [IMP]rma enable invoicing from settings

[33mcommit 173e625d9a8cc8c1e5a69296e5599d44f35dd171[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Fri Feb 14 12:43:49 2020 +0100

    [FIX]rma_account refund creation

[33mcommit 3ebb73235bffe8a0ab3c88131ae9a7fe2a6e649d[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Fri Feb 14 12:42:47 2020 +0100

    [IMP]rma master data menus

[33mcommit a1b48af9547b76a388498bf1bcb18e47af475bfb[m
Author: hveficent <hector.villarreal@forgeflow.com>
Date:   Mon Jan 20 08:10:19 2020 +0100

    RMA as an APP

[33mcommit d2d7487fee833e3d8e22560aad4c7e258ded3190[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Tue Jan 14 16:42:55 2020 +0100

    [MIG] rma: Migration to 13.0

[33mcommit c7720d32f02dba77a9624eeb7b90b98f711ec63a[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Tue Jan 14 16:36:03 2020 +0100

    [IMP] : black, isort

[33mcommit c8972eb684ff41c1c262b06a782ca6718e06986d[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Fri Jan 3 13:41:25 2020 +0100

    [UPT]rma group report to v12

[33mcommit 3443b973d7145a5a208aa85aa96672d7616389f5[m
Author: Chafique <chafique.delli@akretion.com>
Date:   Fri Dec 6 17:26:22 2019 +0100

    [10.0][IMP]add report for rma group

[33mcommit bcb3a40b635426c3cfdf2bc32d55528675b4510d[m
Author: mreficent <miquel.raich@eficent.com>
Date:   Fri Nov 29 18:30:43 2019 +0100

    [FIX] default_gets: avoid using shadowname 'fields'

[33mcommit 37c80bb7d7e56cbfe65c1646c689d8ff064ad8ad[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Tue Oct 29 16:53:47 2019 +0100

    [FIX]UsreError to Validation Error

[33mcommit cbeb7e96a4c8687ab47fc0c91f39e7d7cebb55cf[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Tue Oct 29 16:36:59 2019 +0100

    [FIX]move constraint from the rma order to the line

[33mcommit a1887b5872126dae96a02e499b3e2154bddbf25e[m
Author: mreficent <miquel.raich@eficent.com>
Date:   Wed Oct 30 19:38:23 2019 +0100

    [FIX] tests

[33mcommit 975f1403e3247dc8a3f17638627e712ba32bea35[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Tue Oct 8 18:05:47 2019 +0200

    [FIX] description on rma models

[33mcommit e3c869f4af9522328eb98c316307114bc2c1056f[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Mon Sep 23 17:45:51 2019 +0200

    [IMP]return qty instead of ordered qty

[33mcommit bbddd29cb577b4f0dc0a664dafe7bd97d35492e0[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Mon Sep 23 14:04:58 2019 +0200

    [FIX]supplier lines field description

[33mcommit db0f6841aee8d5548046b58313f071262925b9fb[m
Author: ahenriquez <ahenriquez@eficent.com>
Date:   Fri Sep 20 11:33:55 2019 +0200

    [ENH]activate description also fro customer RMAs
    [ENH]add term and conditions field to be printed and send to the partner
    [FIX]do not show rma groups on the rma line form view if they are not activated

[33mcommit 86630191e5aa4994d8588aeb574d4ac711a6d9a2[m
Author: Aaron Henriquez <ahenriquez@eficent.com>
Date:   Mon Jul 15 11:43:23 2019 +0200

    [FIX]consistency group vs line in the picking count methods

[33mcommit c81644575ba56a9ab09b2b2d14a7088e2d652a0f[m
Author: Aaron Henriquez <ahenriquez@eficent.com>
Date:   Tue Jul 16 12:40:21 2019 +0200

    [FIX]wizard to create pickings, not to show rma groups if rma groups are not activated

[33mcommit cfbc1e6901ef9c8765b50a9041a5f024fe923447[m
Author: Aaron Henriquez <ahenriquez@eficent.com>
Date:   Thu Jul 11 16:39:50 2019 +0200

    [FIX]do not copy name when duplicating

[33mcommit 22953ac064c75a3e571366682b6cd6e17211c5fb[m
Author: Alexandre Fayolle <alexandre.fayolle@camptocamp.com>
Date:   Fri Jun 21 14:47:51 2019 +0200

    make the RMA routes shared in multicompany by default

[33mcommit 7488ef974b89e75e09595e7d0cdd8cb38969ae61[m
Author: Alexandre Fayolle <alexandre.fayolle@camptocamp.com>
Date:   Fri Jun 21 14:36:00 2019 +0200

    [FIX] wrong company on stock rules

    when working with odoobot account, you would get the wrong company_id
    on the RMA stock.rules of the warehouse on which you enabled RMA

[33mcommit 755ee3fcdcd61b6f7fa7f9fa08316f147efe7042[m
Author: Alexandre Fayolle <alexandre.fayolle@camptocamp.com>
Date:   Fri Jun 21 09:58:58 2019 +0200

    [IMP] rma operation form view

    use the archive button in the form view, rather than
    a normal boolean field.

[33mcommit 7a20de67363f3ea0aeb77a97d4ac14af6e19d10c[m
Author: Alexandre Fayolle <alexandre.fayolle@camptocamp.com>
Date:   Wed Jun 19 00:10:34 2019 +0200

    [FIX] multicompany security

    the rma module had company_id fields on rma.order and rma.order.line but not on rma.operation,
    and no global multicompany record rules.

    -> we fix this and avoid a mess with people allowed to see an operation in the drop down list
    but unable to use it because if points to a warehouse of another company

[33mcommit bc33d8e7a0209dfaac60dff531cceda1a36833bb[m
Author: Bhavesh Odedra <bodedra@ursainfosystems.com>
Date:   Wed Jun 5 19:12:06 2019 +0530

    [FIX] Class typo, ProcurementRule is StockRule in V12.0

[33mcommit fc1fc7177045cac6bdff0f0c900e6fef27d5124f[m
Author: Bhavesh Odedra <bodedra@ursainfosystems.com>
Date:   Fri May 24 13:28:54 2019 +0530

    [SET] Correct website URL for RMA modules

[33mcommit 5ad6741ceb6ff3e38691ea8193bbc2bc29b913ef[m
Author: Akim Juillerat <akim.juillerat@camptocamp.com>
Date:   Wed Apr 10 15:02:52 2019 +0200

    [FIX] Remove picking_id from default_get as model does not define it

[33mcommit ec595c9cea4dc3c8cae2d1cf77c30bdc8d77c36f[m
Author: Akim Juillerat <akim.juillerat@camptocamp.com>
Date:   Mon Mar 18 18:13:25 2019 +0100

    Define default value for required fields

[33mcommit b87ccca333e0514191abba471c9b33384247a2bf[m
Author: Akim Juillerat <akim.juillerat@camptocamp.com>
Date:   Mon Mar 18 17:38:46 2019 +0100

    Use strings on fields compute to allow inheritance

[33mcommit 0b8eaeada4f0a4e624d0b92f5ad178ea2f11f057[m
Author: Akim Juillerat <akim.juillerat@camptocamp.com>
Date:   Mon Mar 18 17:31:56 2019 +0100

    Proxy fields defaults with lambda to allow inheritance

[33mcommit 34540b0cf40835e2c5e99bb9ba7739520d389415[m
Author: Akim Juillerat <akim.juillerat@camptocamp.com>
Date:   Tue Mar 12 18:59:47 2019 +0100

    rma: Fix stock_location res.groups

[33mcommit 4b783c29a184edb62b71d17db20d57553d4d5e40[m
Author: Beñat Jimenez <benat.jimenez@eficent.com>
Date:   Thu Feb 14 09:28:48 2019 +0100

    [FIX] qty_delivered is not updated properly

[33mcommit 764075c8cb95a09afff37442d530dad6f7b74fe6[m
Author: Adrià Gil Sorribes <adria.gil@eficent.com>
Date:   Mon Dec 3 13:01:03 2018 +0100

    [12.0][FIX] Fix search view in rma module

[33mcommit 3dc6c67542d05f6bc7d0b5d1fc32a8d92c8056ca[m
Author: Adrià Gil Sorribes <adria.gil@eficent.com>
Date:   Mon Nov 19 16:53:43 2018 +0100

    [12.0][MIG] Migrate rma module to v12.0

[33mcommit 5658fcc32f5416422b489341c9a826296c7d5832[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Thu Oct 4 16:26:45 2018 +0200

    [UPT]report usable in v11

[33mcommit 82e90ece75ea2696a8466c8fb27011f056e350e5[m
Author: aaron <ahenriquez@eficent.com>
Date:   Fri May 25 15:34:39 2018 +0200

    [IMP]add rma line report

[33mcommit d18758210ef9ea0ddbc1076fc0a04eb0f83fb6ae[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Thu Oct 4 12:10:51 2018 +0200

    [FIX]text on create supplier rma button

[33mcommit 306ff7586df82389504143dc7aecaea7f3e33842[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Fri Aug 24 10:18:30 2018 +0200

    [IMP]add icon. Courtesy lreficent.

[33mcommit 6a52a708585825ef06e9277ac2753f70f3b4d1cd[m
Author: aaron <ahenriquez@eficent.com>
Date:   Thu May 24 11:50:28 2018 +0200

    [FIX]RMA location company is the warehouse company

[33mcommit cba83e69f01b9711ea8465041f30229b7feaee4e[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Fri Aug 3 11:24:58 2018 +0200

    [IMP] add group to manage rma groups

[33mcommit e16a91f316473945abaf49d4cc3037a4c343f981[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Fri Aug 3 11:01:09 2018 +0200

    [IMP]product first on view then select document according to product

[33mcommit 6bd70721227aa5c261739a88853912de9c0955ef[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Mon Jul 30 18:37:35 2018 +0200

    [FIX]rma test

[33mcommit 78b1f4c4e631b8b04e1065c3fa5b4300b9418276[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Mon Jul 30 18:37:14 2018 +0200

    [FIX]compute_qty_to_receive

[33mcommit 361c7ad31aee0ccb0305876160185f92b6f2f7c8[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Mon Jul 30 18:36:49 2018 +0200

    [FIX]views rma

[33mcommit 6e9092a277e0bbf4bd1f3f70eaab17e3827076e9[m
Author: Lois Rilo <lois.rilo@eficent.com>
Date:   Mon May 14 17:05:57 2018 +0200

    [9.0][IMP] rma: tests moved to Savedpointcase and optimized (66% time reduction)

[33mcommit 0dd045d27a4668e50de74de2dca315fbeff08fb6[m
Author: Lois Rilo <lois.rilo@eficent.com>
Date:   Fri Aug 3 12:48:52 2018 +0200

    [9.0][IMP] rma: configuring rma for a warehouse from the wh form view

[33mcommit f7f3e960a118ec783f93b826316359cafbefaf8b[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Thu Jul 26 18:41:44 2018 +0200

    [MIG]rma v110.0.2.0.0

[33mcommit 92e1033c9f72d1bdeaa706542aed3fffb46627b8[m
Author: Maxime Chambreuil <mchambreuil@opensourceintegrators.com>
Date:   Wed Jun 27 08:09:46 2018 -0500

    [FIX] Access rights with group deps

[33mcommit 4de6a2d1b696d0768d6dccecfe7f5a6341d9aa4d[m
Author: Maxime Chambreuil <mchambreuil@opensourceintegrators.com>
Date:   Tue Jun 26 12:02:00 2018 -0500

    [FIX] Add read access to stock.move

[33mcommit 4571901891f9e85af618d48b2d7be22e07a92bf0[m
Author: Bhavesh Odedra <bodedra@ursainfosystems.com>
Date:   Thu Jul 19 20:08:43 2018 +0530

    [FIX] TypeError: unhashable type: 'list'

[33mcommit 7c7b1ad38cab689e66db4ecd8ad1f3348b160ed6[m
Author: Maxime Chambreuil <mchambreuil@opensourceintegrators.com>
Date:   Wed Jun 27 08:09:46 2018 -0500

    [FIX] Access rights with group deps

[33mcommit 8ca44fbabecebec97e2d7bfa5a1324b5245599d2[m
Author: Maxime Chambreuil <mchambreuil@opensourceintegrators.com>
Date:   Tue Jun 26 12:02:00 2018 -0500

    [FIX] Add read access to stock.move

[33mcommit 0c9abac186cf18a4cb9d1185d73d469edced17da[m
Author: Maxime Chambreuil <mchambreuil@opensourceintegrators.com>
Date:   Mon Jun 25 12:04:11 2018 -0500

    [FIX] Cannot create partner

[33mcommit 020583b8606802140f119be59db6c97046279de1[m
Author: Bhavesh Odedra <bodedra@ursainfosystems.com>
Date:   Wed Feb 14 19:22:41 2018 +0530

    [IMP] Various improvements

[33mcommit 216891b1a9b4ba6f5478a1a6af618c4733933b2a[m
Author: Jordi Ballester <jordi.ballester@eficent.com>
Date:   Wed Feb 14 13:35:09 2018 +0100

    multiple fixes

[33mcommit 3367ce78e4a5ebb12f3f7ca725adf18761ef6a6f[m
Author: Maxime Chambreuil <mchambreuil@opensourceintegrators.com>
Date:   Fri Feb 9 16:52:31 2018 -0600

    [FIX] Errors from tests

[33mcommit 0844d0cebd2da412c9418bff3d1a27a96f0b32a7[m
Author: Maxime Chambreuil <mchambreuil@opensourceintegrators.com>
Date:   Fri Feb 9 12:35:23 2018 -0600

    [MIG] Migrate configuration and cleanup

[33mcommit 5bfa9d13235acbca9d50c7e477194516217622e3[m
Author: Maxime Chambreuil <mchambreuil@opensourceintegrators.com>
Date:   Fri Feb 9 12:24:45 2018 -0600

    [FIX] Permissions and remove (en)coding

[33mcommit c663cd2db232926abc91976f3fc35000f70d6fe3[m
Author: Bhavesh Odedra <bodedra@ursainfosystems.com>
Date:   Fri Feb 9 21:56:28 2018 +0530

    [11.0] MIG: RMA module

[33mcommit 87fadd1d84c7a8f6231397fb23c71576c89b1ad1[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Fri Jan 26 18:03:28 2018 +0100

    [FIX]compute qty when stock moves but not procurements

[33mcommit 138ea708bacc6d0f7ff03c8bd019e61c3dba4cfe[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Mon Jan 22 11:46:33 2018 +0100

    [FIX]moved_qty uses moves not procurements

[33mcommit 1c213466140b3c24567b2bd6e55ca8b93dca64c8[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Tue Jan 9 14:02:51 2018 +0100

    [MIG]rma_operating_unit to v10

[33mcommit 66f741001d0476067173019a72e75f6ef9ba6de1[m
Author: Nikul Chaudhary <nikul.chaudhary.serpentcs@gmail.com>
Date:   Tue Jan 9 15:35:29 2018 +0530

    [IMP] Improved Code.

[33mcommit 4bf794bb1cd7a4f5a3c73e2e0d1e0900c11f95e6[m
Author: Nikul Chaudhary <nikul.chaudhary.serpentcs@gmail.com>
Date:   Fri Jan 5 16:43:54 2018 +0530

    [MIG] Migrated UT & Fixed Travis

[33mcommit f2b5680307cd0945f5ad8824da1c1386626a196b[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Mon Jan 8 16:18:47 2018 +0100

    [FIX]error in compute method

[33mcommit 4096024e0e93b9b18884fa556ea9162bc46ef009[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Tue Jan 2 13:05:09 2018 +0100

    [FIX]various fixes

[33mcommit 5ea392345a13eefea324258a72d0cb4d2cfdd286[m
Author: Nikul Chaudhary <nikul.chaudhary.serpentcs@gmail.com>
Date:   Fri Nov 10 12:48:55 2017 +0530

    [IMP] Improved Unit Test Case and Fixed Travis

[33mcommit 97cb9aff5e2aa27f7bec49fd1c0f8c6c419296f6[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Thu Dec 21 12:44:57 2017 +0100

    [FIX]view

[33mcommit ae8548d234e12819ce90be3864cb2665a3ad5af0[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Tue Dec 19 16:38:50 2017 +0100

    [MIG]rma v10

[33mcommit 0dfeb120e045dcc11811a3cf8755ce8ebb94c30e[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Thu Nov 9 17:48:55 2017 +0100

    [9.0][FIX] rma: create supplier rma wizard

[33mcommit f3c592a1bab23408217ab2f08572ba07fe5b3ed0[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Wed Oct 25 13:59:19 2017 +0200

    [9.0] add under_warranty field

[33mcommit 2947a87e7b180269dc67fd9244bb64e7505487ed[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Mon Oct 23 14:00:01 2017 +0200

    add partner constrain

[33mcommit 30cbd0bdddd689472e0855e4cad6a778a1cf614b[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Mon Oct 23 13:24:59 2017 +0200

    [9.0][IMP] rma: add button to rma's from customers

[33mcommit eb2b47e88f0fa5b3a35d0529af4776b81b82f148[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Thu Oct 19 16:06:45 2017 +0200

    fix rma

[33mcommit 7f14ff8377870df86d35165feee079519adab29f[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Thu Oct 19 11:12:20 2017 +0200

    [9.0][FIX] rma: wizard

[33mcommit 7aea0713d618cff906c3304b33205cca5933e54b[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Thu Oct 19 10:10:19 2017 +0200

    [9.0][IMP] rma: add constrains

[33mcommit 3c0e629f5706b2e51f3bbd78eb6d3e0d2eb9ec2c[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Wed Oct 18 12:20:27 2017 +0200

    [9.0][REW] rma: workflow centralized on rma.order.line and the use of rma.order is optional.

[33mcommit 2b15523f2c96e9be94a766862e0fff64a44d184e[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Fri Aug 25 17:03:25 2017 +0200

    [9.0][IMP] rma_purchase:
    * remove unneded copy and ondelete attributes.
    * simplify action_view methods.
    * fix rma line supplier view.
    * fix wizard.
    * extend README.
    * minor extra fixes.

[33mcommit 6df6b80e02e6d7fa3505dff0407e7896b8cfc685[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Fri Aug 25 12:22:53 2017 +0200

    [9.0][IMP] rma_account:
    * remove unneded copy attributes.
    * simplify action_view methods.
    * fix wrong naming.
    * fix misplaced views.
    * fix wrong count and view actions for rma.orders in invoices.
    * fix error when installing the module.
    * remove unneded data update when preparing rma lines from invoice lines.
    * minor extra fixes.

[33mcommit b2de5addd3f8e8c78ffcf6de03d4a1039633248c[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Thu Aug 24 13:33:41 2017 +0200

    [9.0][FIX]
    * rma: receipt_policy selections not matching.
    * rma_sale: fix _prepare_rma_line_from_sale_order_line.

[33mcommit 80a6b0afd251bc243466c2322c04e9181eb80fe2[m
Author: aheficent <ahenriquez@eficent.com>
Date:   Wed Aug 16 12:52:35 2017 +0200

    [IMP] default operation in product and product_categ for customer and supplier
    [IMP]Separate menus for customer and supplier operations
    * Add active field to rma operation
    * Added tests
    * Fix travis
    * Fix create supplier rma from customer rma

[33mcommit 313929206971bef4909f3af93424082b7b453efb[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Wed Aug 2 17:05:58 2017 +0200

    [9.0][FIX] rma:
    * fix assignment of moves.
    * default qty in rma lines.
    * remove account dependency.
    * test and flake8 fixes.

[33mcommit 5e2f6c46d990e35bdc2cf5dcc4d1b8291e2a8ff6[m
Author: lreficent <lois.rilo@eficent.com>
Date:   Wed Aug 2 14:04:18 2017 +0200

    [9.0] rma: remove rma.rule and add that setting to product.category

[33mcommit 8088c3a829fd7c54a43c12f70e45eae303eba8cd[m
Author: Jordi Ballester <jordi.ballester@eficent.com>
Date:   Thu Jul 27 18:17:19 2017 +0200

    init branch

[33mcommit 6d466171cafe11acec38cd84b7b38d867104fe9f[m[33m ([m[1;31morigin/17.0[m[33m, [m[1;32m17.0[m[33m)[m
Author: AaronHForgeFlow <aaron.henriquez@forgeflow.com>
Date:   Tue Nov 7 16:06:08 2023 +0100

    Init branch 17.0
