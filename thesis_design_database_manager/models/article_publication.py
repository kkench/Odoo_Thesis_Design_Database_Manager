from odoo import fields,models

class ArticlePublication(models.Model):
    _name = "article.publication"
    _description = "Main Study/ies of CpE Students"
    # _order = "add_date desc" #order by date on initial open then sort by alphabetical later? 

    name = fields.Char(string="Article Title", required=True)
    state = fields.Selection(string="Course Status",
                            #  required=True,
                             selection=[
                                 ("proposal", "For Proposal"),
                                 ("accepted", "Proposal Defense Completed"),
                                 ("defended", "Final Defense Completed"),
                             ])
    publishing_state = fields.Selection(string="Published Status",#DO WE NEED TO KEEP TRACK OF STATUS OR JUST BOOLEAN
                                        selection=[
                                            ("waiting", "Waiting Confirmation"),
                                            ("confirmed", "Confirmed"),
                                            ("presented", "Presented"),
                                            ("published", "Published") 
                                            ])
            
    course_name = fields.Selection(string="Design/Thesis",
                                    # required=True,
                                    selection=[
                                                ("design", "Design"),
                                                ("thesis", "Thesis")
                                                ])
    abstract = fields.Text(string="Abstract")
    editable_by_viewer = fields.Boolean(string="Viewable by Instructor")

    article_tag_ids = fields.Many2many("article.tag", "article_publication_ids", string="Tags") #split topic-related tags and system tags? (i.e. "Embedded Systems" as "department/spec/type" tag and "Fish"  as "topic focus" tag respectively)
#add res users as teacher account?
#add csv importation