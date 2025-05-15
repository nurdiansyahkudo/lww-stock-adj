from odoo import models, fields, api, _

class StockAdj(models.Model):
    _inherit = 'stock.quant'

    # debit_line = fields.Monetary(string='Debit', store=True)
    # credit_line = fields.Monetary(string='Credit', store=True)
    debit_line = fields.Monetary(string='Debit', compute='_compute_debit_credit_line', store=True)
    credit_line = fields.Monetary(string='Credit', compute='_compute_debit_credit_line', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id', store=True)

    @api.depends('product_id')
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = rec.product_id.currency_id or self.env.company.currency_id

    @api.depends('product_id')
    def _compute_debit_credit_line(self):
        for quant in self:
            debit = credit = 0.0
            # Cari stock.move.line yang terkait dengan product & lot_id dari quant
            move_lines = self.env['stock.move.line'].search([
                ('product_id', '=', quant.product_id.id),
                ('lot_id', '=', quant.lot_id.id),
            ])

            for line in move_lines:
                qty = line.quantity
                price = quant.lot_id.standard_price or 0.0

                from_usage = line.location_id.usage
                to_usage = line.location_dest_id.usage

                if from_usage not in ('internal', 'transit') and to_usage in ('internal', 'transit'):
                    # Incoming stock → DEBIT
                    debit += qty * price
                elif from_usage in ('internal', 'transit') and to_usage not in ('internal', 'transit'):
                    # Outgoing stock → CREDIT
                    credit += qty * price

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
            'domain': [('location_id.usage', 'in', ['internal', 'transit'])],
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