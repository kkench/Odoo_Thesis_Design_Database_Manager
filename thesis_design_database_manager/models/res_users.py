from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_faculty = fields.Boolean("Is a Faculty of CpE", compute='_compute_is_faculty', store=True)
    article_publication_id = fields.Many2many("article.publication","adviser_id",string="Advisee Papers")

    @api.depends('groups_id')
    def _compute_is_faculty(self):
        faculty_adviser_group = self.env.ref('thesis_design_database_manager.group_article_faculty_adviser')
        for user in self:
            user.is_faculty = faculty_adviser_group in user.groups_id
