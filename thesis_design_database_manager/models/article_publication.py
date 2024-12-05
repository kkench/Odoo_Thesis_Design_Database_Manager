from odoo import api,fields,models
from difflib import SequenceMatcher, get_close_matches

class ArticlePublication(models.Model):
    _name = "article.publication"
    _description = "Main Study/ies of CpE Students"
    _sql_constraints = [
        ("check_title", "UNIQUE(name)", "Title must be unique.")
    ]

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
    max_similarity_score = fields.Integer("Max Similarity Score", readonly=True, default=0)
    similarity_score = fields.Float("Title Similarity Score", readonly=True, compute="_compute_related_studies")

    @api.onchange("article_tag_ids")
    def _compute_related_studies(self):
        self.related_score = 0
        self.similarity_score = 0
        if self.article_tag_ids:
            related_articles = self.env['article.publication'].search([
                ('article_tag_ids', 'in', self.article_tag_ids.ids),
                ('id', '!=', self.id)
            ])
            self.related_article_ids = [(6, 0, related_articles.ids)]
            for article in related_articles:
                similar_tags = set(article.article_tag_ids.ids) & set(self.article_tag_ids.ids)
                article.related_score = len(similar_tags)
                seq_match = SequenceMatcher(None, self.name,article.name)
                article.similarity_score = (seq_match.ratio())*100
                if article.related_score > article.max_related_score:
                    article.max_related_score = article.related_score
                if article.similarity_score > self.similarity_score:
                    self.max_similarity_score = article.similarity_score
        else:
            self.related_article_ids = [(5, 0, 0)]

    def act_suggested_tags(self):
        if self.name:
            all_tags = self.env['article.tag'].search([])
            tag_names = [tag.name for tag in all_tags] #get all tags to compare
            
            keywords = self.name.split()
            for word in keywords:
                found_tags = get_close_matches(word, tag_names) #compare all words in sentence to existing tags (up to 3 letters mistake)
            
            suggested_tags = self.env['article.tag'].search([
                ('name', 'in', found_tags),
                ("id","not in", self.article_tag_ids.ids) #all tags in found tags and not currently assigned to this model
                ])
            existing_tags = self.env['article.tag'].search([
                ("id","in",self.article_tag_ids.ids) #all tags currently assigned to this model
            ])
            
            combined_tags = (suggested_tags)|(existing_tags)
            self.article_tag_ids = [(6,0, combined_tags.ids)]
        
        return

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
    


