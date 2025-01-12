#add temporary column for descriptvie tags???
from odoo import models, fields, api
import nltk

class ArticleImportExcelWizard(models.TransientModel):
    _description = "Import Your Article Excel Files"

    _inherit = "article.import.excel.wizard"

    def excel_tags_to_odoo_tags(self, tag_string):
        all_tags = self.env['article.tag'].search([])
        provided_tags = tag_string.split(';')
        return provided_tags        

    def check_abbreviation(self, keywords):
        abbreviations = []
        for tag in keywords:
            if tag.isupper() and len(tag) > 1:
               abbreviations.append(tag)
        return abbreviations
         #([A-Z\S]{2,}+) [A-Z] is all uppercase \S ignore all whitespace {2,}
        #regex for later to make abbreviation checking work better if no correction via menu is implemented

    def act_get_tags(self):
        if not self.wizard_new_records_ids: return #if blank
        for form_record in self.wizard_new_records_ids:
            article_tags = self.excel_tags_to_odoo_tags(form_record.tags)

            abbreviated_tags = self.check_abbreviation(article_tags) #add to the wizard for resolving
            complete_tags = article_tags - abbreviated_tags

            #add similarity check from publication here
            return #return to page 3 tba

    

    # def act_import_new_article_wizard_part3(self):
    #run similarity check, abbreviation check then move to tag adjustment page
        

    def act_import_new_article_wizard_part2(self):
        excel_df = self._get_wizard_df()
        new_article_list = []
        for index, row in excel_df.iterrows():
            #---------Static Article Information--------------
            row_data_dictionary = self._get_initial_temp_data(row)
            if self.user_privilege == "design_instructor":
                row_data_dictionary['course'] = 'D'
            elif self.user_privilege == "thesis_instructor":
                row_data_dictionary['course'] = 'T'
            elif self.user_privilege == "faculty_adviser":
                row_data_dictionary['adviser'] = self.env.user.name
            # print(row['Completion time'])
            # row_data_dictionary['registration_date'] = self.excel_date_to_odoo_date(row['Completion time'])
            #-------------------------------------------------

            #----------Excel to Official Column Information-------------
            for excel_column_record in self.excel_column_ids:
                if not excel_column_record.official_record_id:
                    continue
                row_data_dictionary[self.COLUMNS_FOR_NEW_ARTICLE_DICT[excel_column_record.official_record_id.name]] = row[excel_column_record.name]
            new_article = self.env['article.wizard.publications'].create(row_data_dictionary)
            new_article.tags = self.excel_tags_to_odoo_tags(new_article.tags)
            # new_article._compute_errors_and_id()
            new_article_list.append(new_article.id)
            #------------------------------------------------------------
        self.wizard_new_records_ids = [(6, 0, new_article_list)]
        #for record in wizard_new_record_ids

        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Tag Checking', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part2').id, 'form')],#[(self.env.ref('article_import_excel_wizard_form_view_tags').id, 'form')],  
            'target': 'current', }
        #Not sure if return will override super, but this will move part 2 to the tagging system
        #Make sure to create the new view listed here