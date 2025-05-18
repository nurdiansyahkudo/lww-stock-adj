from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero
import logging

_logger = logging.getLogger(__name__)

class StockAdj(models.Model):
    _inherit = 'stock.quant'

    debit_line = fields.Monetary(string='Debit', compute='_compute_debit_credit_line', store=True)
    credit_line = fields.Monetary(string='Credit', compute='_compute_debit_credit_line', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id', store=True)
    is_custom_adjustment = fields.Boolean(
        string="Custom Adjustment",
        compute="_compute_is_custom_adjustment",
        store=False
    )

    @api.depends_context('params')
    def _compute_is_custom_adjustment(self):
        view_id = self.env.context.get('params', {}).get('view_id')
        custom_view_ref = 'lww_stock_adj.view_stock_quant_tree_inventory_editable_adj'
        custom_view_id = self.env.ref(custom_view_ref, raise_if_not_found=False).id if custom_view_ref else False
        for record in self:
            record.is_custom_adjustment = view_id == custom_view_id

    @api.depends('product_id')
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = rec.product_id.currency_id or self.env.company.currency_id

    @api.depends('lot_id')
    def _compute_debit_credit_line(self):
        for quant in self:
            debit = credit = 0.0
            price = quant.lot_id.standard_price or 0.0
            qty = quant.quantity

            # Logic baru:
            if qty == 1:
                credit = qty * price
            elif qty == 0:
                debit = 1 * price  # diasumsikan 1 masuk (stok awal)

            quant.debit_line = debit
            quant.credit_line = credit

    @api.model
    def action_view_adjustment(self):
        """ Similar to _get_quants_action except specific for inventory adjustments (i.e. inventory counts). """
        self = self._set_view_context()
        self._quant_tasks()

        ctx = dict(self.env.context or {})
        ctx['inventory_mode'] = True
        ctx['inventory_report_mode'] = False
        ctx['no_at_date'] = True
        if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group('stock.group_stock_manager'):
            ctx['search_default_my_count'] = True
        view_id = self.env.ref('lww_stock_adj.view_stock_quant_tree_inventory_editable_adj').id
        action = {
            'name': _('Stock Adjustments'),
            'view_mode': 'list',
            'res_model': 'stock.quant',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'domain': [('location_id.usage', 'in', ['internal', 'transit']), ('is_custom_adjustment', '=', True)],
            'views': [(view_id, 'list')],
            'help': """
                <p class="o_view_nocontent_smiling_face">
                    {}
                </p><p>
                    {} <span class="fa fa-long-arrow-right"/> {}</p>
                """.format(_('Your stock is currently empty'),
                           _('Press the CREATE button to define quantity for each product in your stock or import them from a spreadsheet throughout Favorites'),
                           _('Import')),
        }
        return action
    
    @api.model_create_multi
    def create(self, vals_list):
        # Ambil view ID dari context
        view_id = self.env.context.get('params', {}).get('view_id')
        custom_view_ref = 'lww_stock_adj.view_stock_quant_tree_inventory_editable_adj'
        custom_view = self.env.ref(custom_view_ref, raise_if_not_found=False)
        custom_view_id = custom_view.id if custom_view else False

        is_inventory_mode = self._is_inventory_mode()
        allowed_fields = self._get_inventory_fields_create()

        # Buat quant records sekaligus, sesuai dengan @api.model_create_multi
        quants = super().create(vals_list)

        # Apply custom logic setelah quant dibuat
        for quant, vals in zip(quants, vals_list):
            if 'quantity' in vals and 'inventory_quantity' in vals and vals['quantity'] == vals['inventory_quantity']:
                _logger.warning("Quant %s has no discrepancy, will not trigger stock move on apply", quant.id)

            if custom_view_id and view_id == custom_view_id:
                if is_inventory_mode:
                    if 'inventory_quantity' not in vals and 'quantity' in vals:
                        quant.inventory_quantity = 0.0
                    quant.inventory_quantity_set = True

        return quants
    
    def _apply_inventory(self):
        move_vals = []
        for quant in self:
            # Create and validate a move so that the quant matches its `inventory_quantity`.
            if float_compare(quant.inventory_diff_quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0:
                move_vals.append(
                    quant._get_inventory_move_values(quant.inventory_diff_quantity,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     quant.location_id, package_dest_id=quant.package_id))
            else:
                move_vals.append(
                    quant._get_inventory_move_values(-quant.inventory_diff_quantity,
                                                     quant.location_id,
                                                     quant.product_id.with_company(quant.company_id).property_stock_inventory,
                                                     package_id=quant.package_id))
        moves = self.env['stock.move'].with_context(inventory_mode=False).create(move_vals)
        moves._action_done()
        self.location_id.write({'last_inventory_date': fields.Date.today()})
        date_by_location = {loc: loc._get_next_inventory_date() for loc in self.mapped('location_id')}
        for quant in self:
            quant.inventory_date = date_by_location[quant.location_id]
        self.action_clear_inventory_quantity()
