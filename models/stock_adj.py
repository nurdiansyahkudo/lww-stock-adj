from odoo import models, fields, api, _

class StockAdj(models.Model):
    _name = 'stock.adj'
    _description = 'Stock Adjustment'

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=lambda self: self._domain_product_id(),
        ondelete='restrict', required=True, index=True, check_company=True)
    product_tmpl_id = fields.Many2one(
        'product.template', string='Product Template',
        related='product_id.product_tmpl_id')
    product_uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        readonly=True, related='product_id.uom_id')
    is_favorite = fields.Boolean(related='product_tmpl_id.is_favorite')
    company_id = fields.Many2one(related='location_id.company_id', string='Company', store=True, readonly=True)
    location_id = fields.Many2one(
        'stock.location', 'Location',
        domain=lambda self: self._domain_location_id(),
        auto_join=True, ondelete='restrict', required=True, index=True)
    warehouse_id = fields.Many2one('stock.warehouse', related='location_id.warehouse_id')
    storage_category_id = fields.Many2one(related='location_id.storage_category_id', store=True)
    cyclic_inventory_frequency = fields.Integer(related='location_id.cyclic_inventory_frequency')
    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial Number', index=True,
        ondelete='restrict', check_company=True,
        domain=lambda self: self._domain_lot_id())
    lot_properties = fields.Properties(related='lot_id.lot_properties', definition='product_id.lot_properties_definition', readonly=True)
    sn_duplicated = fields.Boolean(string="Duplicated Serial Number", compute='_compute_sn_duplicated', help="If the same SN is in another Quant")
    package_id = fields.Many2one(
        'stock.quant.package', 'Package',
        domain="['|', ('location_id', '=', location_id), '&', ('location_id', '=', False), '&', ('package_use', '=', 'reusable'), ('quant_ids', '=', False)]",
        help='The package containing this quant', ondelete='restrict', check_company=True, index=True)
    owner_id = fields.Many2one(
        'res.partner', 'Owner',
        help='This is the owner of the quant', check_company=True,
        index='btree_not_null')
    quantity = fields.Float(
        'Quantity',
        help='Quantity of products in this quant, in the default unit of measure of the product',
        readonly=True, digits='Product Unit of Measure')
    reserved_quantity = fields.Float(
        'Reserved Quantity',
        default=0.0,
        help='Quantity of reserved products in this quant, in the default unit of measure of the product',
        readonly=True, required=True, digits='Product Unit of Measure')
    available_quantity = fields.Float(
        'Available Quantity',
        help="On hand quantity which hasn't been reserved on a transfer, in the default unit of measure of the product",
        compute='_compute_available_quantity', digits='Product Unit of Measure')
    in_date = fields.Datetime('Incoming Date', readonly=True, required=True, default=fields.Datetime.now)
    tracking = fields.Selection(related='product_id.tracking', readonly=True)
    on_hand = fields.Boolean('On Hand', store=False, search='_search_on_hand')
    product_categ_id = fields.Many2one(related='product_tmpl_id.categ_id')

    # Inventory Fields
    inventory_quantity = fields.Float(
        'Counted Quantity', digits='Product Unit of Measure',
        help="The product's counted quantity.")
    inventory_quantity_auto_apply = fields.Float(
        'Inventoried Quantity', digits='Product Unit of Measure',
        compute='_compute_inventory_quantity_auto_apply',
        inverse='_set_inventory_quantity', groups='stock.group_stock_manager'
    )
    inventory_diff_quantity = fields.Float(
        'Difference', compute='_compute_inventory_diff_quantity', store=True,
        help="Indicates the gap between the product's theoretical quantity and its counted quantity.",
        readonly=True, digits='Product Unit of Measure')
    inventory_date = fields.Date(
        'Scheduled Date', compute='_compute_inventory_date', store=True, readonly=False,
        help="Next date the On Hand Quantity should be counted.")
    last_count_date = fields.Date(compute='_compute_last_count_date', help='Last time the Quantity was Updated')
    inventory_quantity_set = fields.Boolean(store=True, compute='_compute_inventory_quantity_set', readonly=False, default=False)
    is_outdated = fields.Boolean('Quantity has been moved since last count', compute='_compute_is_outdated', search='_search_is_outdated')
    user_id = fields.Many2one(
        'res.users', 'Assigned To', help="User assigned to do product count.",
        domain=lambda self: [('groups_id', 'in', self.env.ref('stock.group_stock_user').id)])

    @api.model
    def action_view_adjustments(self):
        """Custom stock adjustment view."""
        ctx = dict(self.env.context or {})
        ctx['no_at_date'] = True
        if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group('stock.group_stock_manager'):
            ctx['search_default_my_count'] = True

        tree_view = self.env.ref('stock_adjustment_custom.view_stock_adj_tree').id
        form_view = self.env.ref('stock_adjustment_custom.view_stock_adj_form').id

        action =  {
            'name': _('Stock Adjustments'),
            'view_mode': 'list',
            'res_model': 'stock.adj',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'domain': [('location_id.usage', 'in', ['internal', 'transit'])],
            'views': [(tree_view, 'list')],
            'help': """
                <p class="o_view_nocontent_smiling_face">
                    {}
                </p><p>{}</p>
            """.format(_('No stock adjustments found.'), _('Use CREATE to log a manual stock adjustment.')),
        }
        return action

