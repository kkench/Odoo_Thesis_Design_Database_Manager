from odoo import api,fields,models
from difflib import SequenceMatcher, get_close_matches
from odoo.exceptions import UserError
import re

class ArticlePublication(models.Model):
    _name = "article.publication"
    _description = "Main Studies of CpE Students"
    _sql_constraints = [
        ("check_title", "UNIQUE(name)", "Title must be unique for each publication")
    ]
    #-------Form Requirements--------
    custom_id = fields.Char(string='Custom ID', required=True, default='None', readonly=True)
    name = fields.Char(string="Article Title", required=True)
    state = fields.Selection(string="Course Status",
                             required=True,
                             selection=[
                                ("draft", "Topic Drafted"), # registration
                                ("proposal", "Topic Proposal"),# Need enlistment to get here
                                ("proposal_redefense", "Proposal Redefense"),
                                ("proposal_revision", "Proposal Revision"),
                                ("in_progress", "Under Testing/Prototyping"),
                                ("pre_final_defense", "For Final Defense Enlistment"),# Passing T2/D2 Enlistment
                                ("final_defense", "Final Defense"),# Need Enlistment to Get here
                                ("final_redefense", "For Final Redefense"),
                                ("final_revisions", "For Final Revision"),
                                ("article_2_approval_request", "Awaiting Approval of Article 2"), #For Article 2 Only
                                ("accepted", "Topic Complete"),
                                ("rejected", "Rejected"),
                                ("voided", "Voided"),
                             ],default="draft")

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
    onedrive = fields.Text(string="Onedrive Link")
    date_registered = fields.Date(string="Day of Registration") 
    author1 = fields.Char("Author 1",default=None)
    author2 = fields.Char("Author 2",default=None)
    author3 = fields.Char("Author 3",default=None)
    article2_flag = fields.Boolean("Is an Article 2",default=False)
    adviser_ids = fields.Many2many(
        "res.users",
        "article_publication_res_users_rel",
        "publication_id",
        "user_id",
        string="Advisers",
        domain=lambda self: [('groups_id', 'in', [self.env.ref('thesis_design_database_manager.group_article_faculty_adviser').id])], required=True
        )
    
    popup_message = fields.Char("Warning", readonly=True)
    doi = fields.Char("DOI", default=None)

    article_tag_ids = fields.Many2many("article.tag", "article_publication_ids", string="Tags",)
    replacement_identifier = fields.Char("Replacement ID After Member Change", compute="_compute_temp_id")
    latest_student_batch_yr = fields.Integer("Latest Batch Year From All Members")

    authors = fields.Char("Authors", compute="_compute_combined_authors", store=True)
    #-----Computable Information------
    is_article_adviser = fields.Boolean(string="The user is the adviser of the paper", compute="_compute_article_editability")
    is_course_instructor = fields.Boolean(string="The user is the instructor of the paper", compute="_compute_article_editability")

    related_article_ids = fields.Many2many("article.publication", "related_article_ids", readonly=True, string="Related Studies", compute="_compute_related_studies") 
    tag_similarity_score = fields.Integer("Related Score", readonly=True, compute="_compute_related_studies")
    max_tag_similarity_score = fields.Integer("Max Related Score", readonly=True, default=0)
    
    max_title_similarity_score = fields.Integer("Max Similarity Score", readonly=True, default=0)
    title_similarity_score = fields.Float("Title Similarity Score", readonly=True, compute="_compute_related_studies")


    @api.depends('author1','author2','author3')
    def _compute_combined_authors(self):
        for record in self:
            # if not (record.id and isinstance(record.id, int)):
            #     continue
            record.authors = ' '.join(filter(None, [record.author1, record.author2, record.author3]))

    @api.depends("course_name","adviser_ids")
    def _compute_article_editability(self):
        user = self.env.user
        user_is_instructor_dictionary = {
                        "thesis": user.has_group('thesis_design_database_manager.group_article_thesis_instructor'),
                        "design": user.has_group('thesis_design_database_manager.group_article_design_instructor')
                        }

        for record in self:
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
    @api.onchange('doi')
    def _onchange_doi_status(self):
        if self.doi:
            self.publishing_state = "published"
        elif not self.doi:
            self.publishing_state = "not_published"
    
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


    #----Actions-----

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
            'target': 'new',
            'views': [(self.env.ref('thesis_design_database_manager.article_publication_form_view').id, 'form')], 
        }
    
    def act_reject_defense(self):
        return self.write({'state':'rejected'})

    def act_accept_defense(self):
        if self.state == 'proposal':
            return self.write({'state':'in_progress'})
        if self.state == 'final_defense':
            return self.write({'state':'accepted'})
        
    def act_minor_revisions_defense(self):
        if self.state == 'proposal':
            return self.write({'state':'proposal_revision'})
        if self.state == 'final_defense':
            return self.write({'state':'final_revisions'})

    def act_redef_defense(self):
        if self.state == 'proposal':
            return self.write({'state':'proposal_redefense'})
        if self.state == 'final_defense':
            return self.write({'state':'final_redefense'})
        
    def act_initial_proto_demo(self):
        if self.state == 'in_progress':
            return self.write({'state':'pre_final_defense'})

        
        
    def act_member_change(self):
        if self.state == "voided":
            raise UserError("This topic is already voided. Members cannot be changed.")
        self.replacement_identifier = None
        return {
            'type': 'ir.actions.act_window',
            'name': 'Member Change Form',
            'view_mode': 'form',
            'res_model': 'article.publication',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_publication_member_change_form_view').id, 'form')], 
            'target': 'new',
        }

    @api.onchange("author1","author2","author3","latest_student_batch_yr","article2_flag")
    def _compute_temp_id(self):
        if not (self.latest_student_batch_yr>=2010 and self.latest_student_batch_yr<2999): 
            self.replacement_identifier = "Year Ivalid"
            return

        if not self.is_author_name_valid(): 
            self.replacement_identifier = "Name Invalid"
            return

        course_code = 'T' if self.course_name == "thesis" else 'D'
        if course_code == 'T':
            article_string = 'Art2' if self.article2_flag else 'Art1'
        else:
            article_string = None

        self.arrange_lastname_alphabetically()
        temp_last_names = self._get_lastnames()
        student_batch_num = str(self.latest_student_batch_yr)
        separator = '_'
        id_part_list = [part for part in [temp_last_names, student_batch_num, course_code, article_string] 
                        if part is not None]    
        self.replacement_identifier = separator.join(id_part_list)

    def act_save_new_members(self):
        if self.env['article.publication'].search([('custom_id', '=', self.replacement_identifier)]):
            raise UserError("Students have already existing records")
        return self.write({
            'custom_id':self.replacement_identifier,
        })
    
    def act_void_topic_confirm(self):
        self.ensure_one()
        return {
            'name': 'Void Topic',
            'type': 'ir.actions.act_window',
            'res_model': 'article.publication',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('thesis_design_database_manager.article_publication_voiding_confirmation_popup_form').id,
            'target': 'new',
        }
        
    def act_void_topic(self):
        self.ensure_one()
        if self.custom_id == "":
            raise UserError("Topic is already voided.")
        else:
            return self.write({
            'custom_id':"Voided", 'state':"voided"
        })
    
    def act_redirect_doi(self):
        self.ensure_one()
        doi_string = "https://doi.org/" + self.doi
        return {
            'name': 'Go to Link',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': doi_string,
        }

    def act_deny_topic_defense(self):
        # self.ensure_one()
        for record in self:
            print("Naming:",record.name)
            if record.state == 'proposal':
                record.write({'state': 'draft'})
                print("test1")
            elif record.state == 'final_defense':
                print("test2")
                record.write({'state': 'pre_final_defense'})
            else:
                raise UserError('Topic is Not in Defense')
    
    def _get_lastnames(self):
        #will not account for arrangement of names
        lastname_list = [name.split(",")[0] for name in [self.author1,self.author2,self.author3] if name]
    
        lastname_combination_string = "".join(lastname_list)
        print(lastname_combination_string)
        return lastname_combination_string


    def arrange_lastname_alphabetically(self):
        author_names = [name for name in [self.author1, self.author2, self.author3] if name]
        sorted_names = sorted(author_names)

        sorted_names.extend([None] * (3 - len(sorted_names)))
        if sorted_names == [self.author1, self.author2, self.author3]:
            return [self.author1, self.author2, self.author3]
        else:
            self.author1, self.author2, self.author3 = sorted_names
            return sorted_names

    @api.constrains("author1","author2","author3")
    def _check_author_constrains(self):
        if not self.is_author_name_valid():
            raise UserError("Name has incorrect format")


    def is_author_name_valid(self):
        for record in self:
            pattern_name = r'^[A-Z][a-z]+, ([A-Z][a-z]+ )+[A-Z]\.$'  # LN, FN MI
            if not (record.author1 or record.author2 or record.author3): return False
            for author_name in [record.author1, record.author2, record.author3]:
                if not author_name: continue
                if not re.match(pattern_name, author_name):
                    return False
        return True