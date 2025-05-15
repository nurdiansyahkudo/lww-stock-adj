from odoo import models, fields, api, _

class StockAdj(models.Model):
    _inherit = 'stock.quant'

    debit_line = fields.Monetary(string='Debit', compute='_compute_debit_credit_line', store=True)
    credit_line = fields.Monetary(string='Credit', compute='_compute_debit_credit_line', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id', store=True)
    is_adjustment_line = fields.Boolean(string='Adjustment Line', default=False)

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
        ctx['no_at_date'] = True
        if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group('stock.group_stock_manager'):
            ctx['search_default_my_count'] = True
        view_id = self.env.ref('lww_stock_adj.view_stock_adj_tree_custom').id
        action = {
            'name': _('Stock Adjustments'),
            'view_mode': 'list',
            'res_model': 'stock.quant',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'domain': [('location_id.usage', 'in', ['internal', 'transit']), ('is_adjustment_line', '=', True)],
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
    
    def _get_inventory_fields_create(self):
        fields = super()._get_inventory_fields_create()
        fields.append('is_adjustment_line')
        return fields
    
    @api.model_create_multi
    def create(self, vals_list):
        # Jika context ada view_id yang sesuai dengan custom view, tandai is_adjustment_line
        view_id = self.env.context.get('params', {}).get('view_id')
        custom_view_ref = 'lww_stock_adj.view_stock_adj_tree_custom'
        custom_view_id = self.env.ref(custom_view_ref).id if self.env.ref(custom_view_ref, raise_if_not_found=False) else False

        for vals in vals_list:
            if custom_view_id and view_id == custom_view_id:
                vals['is_adjustment_line'] = True
        return super().create(vals_list)