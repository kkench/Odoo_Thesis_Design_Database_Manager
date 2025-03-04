from odoo import api,models, fields
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = "res.users"

    article_publication_ids = fields.Many2many(
        "article.publication",
        "article_publication_res_users_rel",
        "user_id",
        "publication_id",
        string="Article Publications", readonly=True
    )

    conformity_publication_filter_ids = fields.Many2many(
        "article.publication",
        "article_publication_conformity_filter_rel",
        string="Articles For Conformity", readonly=True,
        compute="_compute_conformity_publications"
    )

    @api.depends("article_publication_ids","conformity_publication_filter_ids")
    def _compute_conformity_publications(self):
        for record in self:
            conformity_articles = record.article_publication_ids.filtered(lambda a: a.state in ['proposal_minor_revisions','final_minor_revisions'])
            record.conformity_publication_filter_ids = conformity_articles

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
    
    def act_shutdown_rpi(self):
        # import os
        def is_raspberry_pi():
            try:
                with open('/sys/firmware/devicetree/base/model', 'r') as model_file:
                    model = model_file.read().strip()
                    if 'Raspberry Pi 4' in model:
                        return True
            except FileNotFoundError:
                return False

        def get_os_info():
            try:
                with open('/etc/os-release', 'r') as os_file:
                    os_info = os_file.read().strip()
                    return os_info
            except FileNotFoundError:
                return "OS information not found"
        
        if not is_raspberry_pi():
            raise UserError("This only works on RPI Systems")
        else:
            raise UserError("IS RPI but not implemented")