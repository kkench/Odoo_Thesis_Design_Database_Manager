from odoo import api,fields,models
from difflib import SequenceMatcher, get_close_matches
from odoo.exceptions import UserError

class ArticlePublication(models.Model):
    _name = "article.publication"
    _description = "Main Studies of CpE Students"
    _sql_constraints = [
        ("check_title", "UNIQUE(name)", "Title must be unique.")
    ]
    #-------Form Requirements--------
    custom_id = fields.Char(string='Custom ID', readonly=True, required=True)
    name = fields.Char(string="Article Title", required=True)
    state = fields.Selection(string="Course Status",
                             required=True,
                             selection=[
                                 ("proposal", "For Proposal"),
                                 ("proposal_approved", "Proposal Approved"),
                                 ("proposal_redefense", "Proposal Redefense Required"),
                                 ("proposal_conformity_of_revisions", "Proposal Conformity of Revisions"),
                                 ("final_approved", "Article Approved"),
                                 ("final_redefense", "Final Redefense Required"),
                                 ("final_conformity_of_revisions", "Final Conformity of Revisions"),
                             ],default="proposal")

    publishing_state = fields.Selection(string="Published Status",
                                        selection=[
                                            ("not_published", "Not Published"),
                                            ("published", "Published") 
                                            ],default="not_published", required=True)
          
    course_name = fields.Selection(string="Course",
                                    required=True,
                                    selection=[
                                                ("design", "Design"),
                                                ("thesis", "Thesis")
                                                ],
                                    default="thesis")
    abstract = fields.Text(string="Abstract", required=True)
    date_registered = fields.Date(string="Day of Registration") 
    author1 = fields.Char("Author 1",default=None)
    author2 = fields.Char("Author 2",default=None)
    author3 = fields.Char("Author 3",default=None)
    adviser_ids = fields.Many2many(
        "res.users",
        "article_publication_res_users_rel",
        "publication_id",
        "user_id",
        string="Advisers",
        domain=lambda self: [('groups_id', 'in', [self.env.ref('thesis_design_database_manager.group_article_faculty_adviser').id])], required=True
        )

    article_tag_ids = fields.Many2many("article.tag", "article_publication_ids", string="Tags",)

    #-----Computable Information------
    is_article_adviser = fields.Boolean(string="The user is the adviser of the paper", compute="_compute_article_editability")
    is_course_instructor = fields.Boolean(string="The user is the instructor of the paper", compute="_compute_article_editability")

    related_article_ids = fields.Many2many("article.publication", "related_article_ids", readonly=True, string="Related Studies", compute="_compute_related_studies") 
    tag_similarity_score = fields.Integer("Related Score", readonly=True, compute="_compute_related_studies")
    max_tag_similarity_score = fields.Integer("Max Related Score", readonly=True, default=0)
    
    max_title_similarity_score = fields.Integer("Max Similarity Score", readonly=True, default=0)
    title_similarity_score = fields.Float("Title Similarity Score", readonly=True, compute="_compute_related_studies")

    @api.depends("course_name","adviser_ids")
    def _compute_article_editability(self):
        user = self.env.user
        user_is_instructor_dictionary = {
                        "thesis": user.has_group('thesis_design_database_manager.group_article_thesis_instructor'),
                        "design": user.has_group('thesis_design_database_manager.group_article_design_instructor')
                        }

        for record in self:
            print("GOT HERE")
            record.is_course_instructor = user_is_instructor_dictionary.get(record.course_name, False)
            record.is_article_adviser = user.id in record.adviser_ids.ids

    @api.onchange('article_tag_ids')
    def _compute_related_studies(self):
        self.tag_similarity_score = 0
        self.title_similarity_score = 0
        if self.article_tag_ids:
            if self.id and isinstance(self.id, int):
                related_articles = self.env['article.publication'].search([
                    ('article_tag_ids', 'in', self.article_tag_ids.ids),
                    ('id', '!=', self.id)
                ])
                self.related_article_ids = [(6, 0, related_articles.ids)]
                for article in related_articles:
                    similar_tags = set(article.article_tag_ids.ids) & set(self.article_tag_ids.ids)
                    article.tag_similarity_score = len(similar_tags)
                    seq_match = SequenceMatcher(None, self.name,article.name)
                    article.title_similarity_score = (seq_match.ratio())*100
                    if article.tag_similarity_score > self.max_tag_similarity_score:
                        self.max_tag_similarity_score = article.tag_similarity_score
                    if article.title_similarity_score > self.max_title_similarity_score:
                        self.max_title_similarity_score = article.title_similarity_score
            else:
                self.related_article_ids = [(5, 0, 0)]
        else:
            self.related_article_ids = [(5, 0, 0)]
    
    @api.constrains('author3')
    def _check_author3_eligability(self):
        for record in self:
            if (not record.author3) or (record.course_name == "design"):
                continue
            raise UserError("Thesis Can Only Have Two Authors")
        
    @api.model
    def default_get(self, fields_list): 
        res = super(ArticlePublication, self).default_get(fields_list)
        # Customize the default value based on the current user
        if self.env.user.has_group('thesis_design_database_manager.group_article_thesis_instructor'):
            res['course_name'] = 'thesis'
        if self.env.user.has_group('thesis_design_database_manager.group_article_design_instructor'):
            res['course_name'] = 'design'
        return res


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