from odoo import models, fields, api, _

class StockAdj(models.Model):
    _name = 'stock.adj'
    _description = 'Stock Adjustment'
    _inherits = {'stock.quant': 'quant_id'}

    quant_id = fields.Many2one('stock.quant', required=True, ondelete='cascade')

    @api.model
    def action_view_adjustments(self):
        """Custom stock adjustment view."""
        ctx = dict(self.env.context or {})
        ctx['no_at_date'] = True
        if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group('stock.group_stock_manager'):
            ctx['search_default_my_count'] = True

        tree_view = self.env.ref('stock_adjustment_custom.view_stock_adj_tree').id
        form_view = self.env.ref('stock_adjustment_custom.view_stock_adj_form').id

        return {
            'name': _('Stock Adjustments'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.adj',
            'view_mode': 'list',
            'views': [(tree_view, 'list')],
            'context': ctx,
            'domain': [('id', '!=', 0)],
            'help': """
                <p class="o_view_nocontent_smiling_face">
                    {}
                </p><p>{}</p>
            """.format(_('No stock adjustments found.'), _('Use CREATE to log a manual stock adjustment.')),
        }

