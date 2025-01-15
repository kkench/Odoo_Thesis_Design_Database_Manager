from odoo import api,fields,models
from difflib import get_close_matches

class ArticleImportExcelWizard(models.TransientModel):
    _description = "Import Your Article Excel Files"

    _inherit = "article.wizard.publication"
    checking_wizard_id = fields.Many2one("article.import.excel.wizard")
    for_checking_tags_ids = fields.Many2many("article.wizard.publication.tag")

    tags_to_create = []

    def tags_are_valid(self):
        article_tags = self.excel_tags_to_odoo_tags(self.tags)
        invalid_tags = self.get_tag_changes(article_tags)
        return invalid_tags

    @staticmethod
    def excel_tags_to_odoo_tags(tag_string):
        provided_tags = []
        provided_tags = tag_string.split(';')
        return provided_tags  

    @staticmethod
    def check_abbreviation(keywords):
        abbreviations = []
        for tag in keywords:
            if (tag.isupper() and (len(tag) > 1)):
               abbreviations.append(tag)
        return abbreviations
         #([A-Z\S]{2,}+) [A-Z] is all uppercase \S ignore all whitespace {2,}
        #regex for later to make abbreviation checking work better if no correction via menu is implemented

    def check_similar_tags(self, keywords):
        similar_tags = []
        tags_to_create = []
        all_tags = self.env['article.tag'].search([])
        tag_names = [tag.name for tag in all_tags]
        for tag in keywords:
            found_tag = get_close_matches(tag, tag_names)
            if not found_tag and tag != "":
                created_tag = self.env["article.wizard.publication.tag"].create({ 'name': tag })
                tags_to_create.append(created_tag.id)
                print(created_tag.name)
            elif any(tag in tag_names for tag in found_tag):
                continue
            else:
                similar_tags.append(found_tag)
        self.for_checking_tags_ids = [(6,0,tags_to_create)]
        return similar_tags

    def get_tag_changes(self, tag_list):
        # self.check_abbreviation(tag_list)
        sim = self.check_similar_tags(tag_list)
        # print(sim)
        if (not sim and not self.for_checking_tags_ids.exists()):
            needs_change = False
        else:
            needs_change = True
        return needs_change
    
class ArticleWizardTempTags(models.TransientModel):
    _name = "article.wizard.publication.tag"

    name = fields.Char("Tag Name")
    article_wizard_publication_ids = fields.Many2many("article.wizard.publication")
    
    