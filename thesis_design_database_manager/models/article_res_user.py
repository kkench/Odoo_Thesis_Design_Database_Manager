from odoo import models, fields

class ResUsers(models.Model):
    _inherit = "res.users"

    article_publication_ids = fields.Many2many(
        "article.publication",
        "article_publication_res_users_rel",
        "user_id",
        "publication_id",
        string="Article Publications", readonly=True
    )

    def act_open_faculty_list(self):
        group = self.env.ref('thesis_design_database_manager.group_article_faculty_adviser')
        faculty_advisers = self.env['res.users'].search([('groups_id', 'in', group.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Adviser List',
            'view_mode': 'tree,form',
            'res_model': 'res.users',
            'domain': [('id', 'in', faculty_advisers.ids)],
            'views': [(self.env.ref('thesis_design_database_manager.article_faculty_adviser_tree_view').id, 'tree'),
                      (self.env.ref('thesis_design_database_manager.article_faculty_adviser_form_view').id, 'form')],  # Replace with your view ID
        }