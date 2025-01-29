from odoo import api,fields,models
from difflib import get_close_matches

class ArticleImportExcelWizard(models.TransientModel):
    _description = "Import Your Article Excel Files"

    _inherit = "article.wizard.publication"
    checking_wizard_id = fields.Many2one("article.import.excel.wizard")
    to_create_tag_ids = fields.Many2many("article.wizard.publication.tag", "article_wizard_pub_new_tags")
    similar_tag_ids = fields.Many2many("article.wizard.publication.tag", "article_wizard_pub_similar_tags")
    existing_tag_ids = fields.Many2many("article.wizard.publication.tag", "article_wizard_pub_existing_tags")

    def tags_are_valid(self):
        if self.tags:
            article_tags = self.excel_tags_to_odoo_tags(self.tags)
            invalid_tags = self.get_tag_changes(article_tags)
        else:
             invalid_tags = [""]
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
        existing_tags = []
        all_tags = self.env['article.tag'].search([])
        tag_names = [tag.name for tag in all_tags]
        for tag in keywords:
            found_tag = get_close_matches(tag, tag_names)
            if found_tag == "" or tag == "":
                    continue
            elif not found_tag:
                    created_tag = self.env["article.wizard.publication.tag"].create({ 'name': tag })
                    tags_to_create.append(created_tag.id)
                    # print(created_tag.name)
            elif tag in found_tag:
                    existing_tag = self.env["article.wizard.publication.tag"].create({ 'name': tag })
                    existing_tags.append(existing_tag.id)
                    # self.link_existing_tag(tag) #link existing temporary tags to real tags
            else:
                    dupli = self.check_duplicate_temp_tags(found_tag) #search duplicates
                    if dupli:
                        similar_tags.append(dupli.id)#link existing tags to real tags 
                        continue
                    else:
                        sim_tag = self.env["article.wizard.publication.tag"].create({ 'name': tag })
                        similar_tags.append(sim_tag.id)
            self.to_create_tag_ids = [(6,0,tags_to_create)]
            self.similar_tag_ids = [(6,0,similar_tags)]
            self.existing_tag_ids = [(6,0,existing_tags)]
            print(similar_tags)
        return similar_tags or existing_tags or tags_to_create

    #Decided not to incorporate because there's no functional difference, even for efficiency
    # def link_existing_tag(self, tag):
    #     existing_tag = self.env['article.tag'].search([tag])
    #     self.existing_tag_ids = [(4,0,existing_tag.id)] #adjust the function in the iwzard as well

    def check_duplicate_temp_tags(self, tag):
        tag_flag = self.env["article.wizard.publication.tag"].search([('name','=',tag)])
        return tag_flag

    def get_tag_changes(self, tag_list):
        # self.check_abbreviation(tag_list)
        sim = self.check_similar_tags(tag_list)
        # print(sim)
        if (not sim and not self.to_create_tag_ids.exists()):
            needs_change = False
        else:
            needs_change = True
        return needs_change
    
class ArticleWizardTempTags(models.TransientModel):
    _name = "article.wizard.publication.tag"

    name = fields.Char("Tag Name")
    article_wizard_publication_ids = fields.Many2many("article.wizard.publication")
    
    