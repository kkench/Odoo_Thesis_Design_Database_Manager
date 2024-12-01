from odoo import api, fields, models

class ArticleInfo(models.Model):
    _name = "article.info"
    _order = "add_date desc" #order by date on initial open then sort by alphabetical later? 

    name = fields.Char(string="Paper Title", required=True)
    #add_date = fields.Date(string="Date Added")
    state = fields.Selection(string="Current Status",
                             required=True,
                             selection=[
                                 ("proposed", "Proposed"),
                                 ("defense1", "Proposal Defense Complete"),
                                 ("defense2", "Final Defense Complete"),
                             ])
    # not sure if it should be boolean publish = fields.Boolean(string="Publication Status") #if published and presented before defended? should probably add function check with status
    publish = fields.Selection(string="Published Status",
                                selection=[
                                    ("waiting", "Waiting Confirmation"),
                                    ("confirmed", "Confirmed"),
                                    ("presented", "Presented"),
                                    ("published", "Published") #merge presented and published? or confirmed and presented
                                    ])
    dt = fields.Selection(string="Design/Thesis",
                          required=True,
                          selction=[
                                    ("design", "Design"),
                                    ("thesis", "Thesis")
                                    ])
    abstract = fields.Text(string="Abstract")
    viewable = fields.Boolean(string="Viewable by Instructor")

    paper_tag_ids = fields.Many2one("paper.info.tags", "paper_tag", string="Tags") #split topic-related tags and system tags? (i.e. "Embedded Systems" as "department/spec/type" tag and "Fish"  as "topic focus" tag respectively)
#add res users as teacher account?
#add csv importation