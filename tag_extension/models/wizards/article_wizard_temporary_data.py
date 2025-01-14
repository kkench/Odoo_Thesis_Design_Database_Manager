from odoo import api,fields,models
from difflib import get_close_matches

class ArticleImportExcelWizard(models.TransientModel):
    _description = "Import Your Article Excel Files"

    _inherit = "article.wizard.publication"
    checking_wizard_id = fields.Many2one("article.import.excel.wizard")


    def tags_are_valid(self):
        article_tags = self.excel_tags_to_odoo_tags(self.tags)
        invalid_tags = self.get_tag_changes(article_tags)
        return invalid_tags

    @staticmethod
    def excel_tags_to_odoo_tags(tag_string):
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
        all_tags = self.env['article.tag'].search([])
        tag_names = [tag.name for tag in all_tags]
        similar_tags = []
        for tag in keywords:
            found_tag = get_close_matches(tag_names, keywords)
            if found_tag == "":
                break
            else:
                similar_tags.append(found_tag)
        return similar_tags

    def get_tag_changes(self, tag_list):
        abbs = self.check_abbreviation(tag_list)
        sim = self.check_similar_tags(tag_list)
        # print(sim)
        if (abbs or sim):
            unchanged = True
        else:
            unchanged = False
        # print(changed)
        return unchanged
    
    