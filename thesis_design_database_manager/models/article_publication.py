from odoo import api,fields,models

class ArticlePublication(models.Model):
    _name = "article.publication"
    _description = "Main Study/ies of CpE Students"

    name = fields.Char(string="Article Title", required=True)
    state = fields.Selection(string="Course Status",
                             required=True,
                             selection=[
                                 ("proposal", "For Proposal"),
                                 ("accepted", "Proposal Defense Completed"),
                                 ("defended", "Final Defense Completed"),
                             ],default="proposal")
    publishing_state = fields.Selection(string="Published Status",#DO WE NEED TO KEEP TRACK OF STATUS OR JUST BOOLEAN
                                        selection=[
                                            ("no_registration", "Not Registered"),
                                            ("waiting", "Waiting Confirmation"),
                                            ("confirmed", "Confirmed"),
                                            ("presented", "Presented"),
                                            ("published", "Published") 
                                            ],default="no_registration")
            
    course_name = fields.Selection(string="Course",
                                    required=True,
                                    selection=[
                                                ("design", "Design"),
                                                ("thesis", "Thesis")
                                                ],
                                    default="thesis")
    abstract = fields.Text(string="Abstract")
    editable_by_viewer = fields.Boolean(string="Viewable by Instructor")

    article_tag_ids = fields.Many2many("article.tag", "article_publication_ids", string="Tags")
    related_article_ids = fields.Many2many("article.publication", "related_article_ids", readonly=True, string="Related Studies", compute="_compute_related_studies") 
    related_score = fields.Integer("Related Score", readonly=True, compute="_compute_related_studies")
    max_related_score = fields.Integer("Max Related Score", readonly=True, default=0)

    @api.onchange('article_tag_ids')
    def _compute_related_studies(self):
        self.related_score = 0
        if self.article_tag_ids:
            if self.id and isinstance(self.id, int):
                related_articles = self.env['article.publication'].search([
                    ('article_tag_ids', 'in', self.article_tag_ids.ids),
                    ('id', '!=', self.id)
                ])
                self.related_article_ids = [(6, 0, related_articles.ids)]
                for article in related_articles:
                    similar_tags = set(article.article_tag_ids.ids) & set(self.article_tag_ids.ids)
                    article.related_score = len(similar_tags)
                    if article.related_score > article.max_related_score:
                        article.max_related_score = article.related_score
                    if article.related_score > self.max_related_score:
                        self.max_related_score = article.related_score
            else:
                self.related_article_ids = [(5, 0, 0)]
        else:
            self.related_article_ids = [(5, 0, 0)]


    def act_view_article(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Article Publication',
            'view_mode': 'form',
            'res_model': 'article.publication',
            'res_id': self.id,
            'target': 'current',
        }

    def act_open_faculty_list(self):
        group = self.env.ref('thesis_design_database_manager.group_article_faculty_adviser')
        faculty_advisers = self.env['res.users'].search([('groups_id', 'in', group.id)])
        # for adviser in faculty_advisers:
        #     print(adviser.name)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Adviser List',
            'view_mode': 'tree',
            'res_model': 'res.users',
            'domain': [('id', 'in', faculty_advisers.ids)],
            'views': [(self.env.ref('thesis_design_database_manager.article_faculty_adviser_tree_view').id, 'tree')],  # Replace with your view ID
        }