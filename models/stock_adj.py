from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero
import logging

_logger = logging.getLogger(__name__)

class StockAdj(models.Model):
    _inherit = 'stock.quant'

    debit_line = fields.Monetary(string='Debit', compute='_compute_debit_credit_line', inverse='_inverse_debit_line', store=True, readonly=False)
    credit_line = fields.Monetary(string='Credit', compute='_compute_debit_credit_line', inverse='_inverse_credit_line', store=True, readonly=False)
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id', store=True)
    is_adj = fields.Boolean(string='Is Adjustment', store=True)

    @api.depends('product_id')
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = rec.product_id.currency_id or self.env.company.currency_id

    @api.depends('lot_id', 'quantity')
    def _compute_debit_credit_line(self):
        for quant in self:
            debit = credit = 0.0
            price = quant.lot_id.standard_price or 0.0
            qty = quant.quantity

            if qty == 1:
                credit = price
            elif qty == 0:
                debit = price

            quant.debit_line = debit
            quant.credit_line = credit

    def _inverse_debit_line(self):
        # Placeholder, bisa diisi logic tambahan jika perlu menyimpan ke tempat lain
        _logger.debug("Inverse debit_line called for %s", self)

    def _inverse_credit_line(self):
        # Placeholder, bisa diisi logic tambahan jika perlu menyimpan ke tempat lain
        _logger.debug("Inverse credit_line called for %s", self)

    @api.model
    def action_view_adjustment(self):
        """ Similar to _get_quants_action except specific for inventory adjustments (i.e. inventory counts). """
        self = self._set_view_context()
        self._quant_tasks()

        ctx = dict(self.env.context or {})
        ctx.update({
            'inventory_mode': True,
            'inventory_report_mode': False,
            'no_at_date': True,
        })

        if self.env.user.has_group('stock.group_stock_user') and not self.env.user.has_group('stock.group_stock_manager'):
            ctx['search_default_my_count'] = True

        view_id = self.env.ref('lww_stock_adj.view_stock_quant_tree_inventory_editable_adj').id
        action = {
            'name': _('Stock Adjustment'),
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
    
    @api.model
    def _get_inventory_fields_write(self):
        """ Returns a list of fields user can edit when he want to edit a quant in `inventory_mode`.
        """
        fields = ['inventory_quantity', 'inventory_quantity_auto_apply', 'inventory_diff_quantity',
                  'inventory_date', 'user_id', 'inventory_quantity_set', 'is_outdated', 'lot_id',
                  'location_id', 'package_id', 'debit_line', 'credit_line']
        return fields