#add temporary column for descriptvie tags???
from odoo import models, fields, api
import nltk

class ArticleImportExcelWizard(models.TransientModel):
    _description = "Import Your Article Excel Files"

    _inherit = "article.import.excel.wizard"

    def check_abbreviation(keywords):
        abbreviations = []
        for tag in keywords:
            if tag.isupper() and len(tag) > 1:
               abbreviations.append(tag)
        return abbreviations

    def excel_tags_to_odoo_tags(tag_string):
        _all_tags = self.env['article.tag'].search([])
        provided_tags = tag_string.split(';')

        abbreviated_tags = self.check_abbreviation(provided_tags)

         #([A-Z\S]{2,}+) [A-Z] is all uppercase \S ignore all whitespace {2,}
        #regex to make abbreviation checking work better if no correction via menu is implemented

        

    

    # def act_import_new_article_wizard_part3(self):
        

    def act_import_new_article_wizard_part2(self):
         # row_data_dictionary['registration_date'] = self.excel_date_to_odoo_date(row['Completion time'])
         #row_data_dictionary[self.COLUMNS_FOR_NEW_ARTICLE_DICT[excel_column_record.official_record_id.name]] = row[excel_column_record.name]
            # new_article = self.env['article.wizard.publications'].create(row_data_dictionary)
            # new_article._compute_errors_and_id()
            # new_article_list.append(new_article.id)
            #figure these out

         return { 
            'type': 'ir.actions.act_window', 
            'name': 'Tag Checking', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_tags').id, 'form')], 
            'target': 'current', }
        #Not sure if return will override super, but this will move part 2 to the tagging system
        #Make sure to create the new view listed here