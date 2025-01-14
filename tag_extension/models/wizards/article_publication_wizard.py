#add temporary column for descriptvie tags???
from odoo import models, fields, api
from difflib import SequenceMatcher, get_close_matches

class ArticleImportExcelWizard(models.TransientModel):
    _description = "Import Your Article Excel Files"
    _inherit = "article.import.excel.wizard"

    wizard_check_tags_records_ids = fields.One2many('article.wizard.publications','checking_wizard_id','List of Records for Checking')

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
            similar_tags.append(found_tag)
        return similar_tags

    def get_tag_changes(self, new_article):
        print(type(new_article.tags))
        tag_list = self.excel_tags_to_odoo_tags(new_article.tags)
        abbs = self.check_abbreviation(tag_list)
        sim = self.check_similar_tags(tag_list)
        if (abbs or sim):
            changed = False
        else:
            changed = True
        new_article.tags = tag_list
        return changed
    
    def get_tags(self):
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
        for_checking_list = []
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
            changed = self.get_tag_changes(new_article)
            if changed:
                for_checking_list.append(new_article.id)
            else:
                new_article_list.append(new_article.id)
            #------------------------------------------------------------
        self.wizard_check_tags_records_ids = [(6, 0, for_checking_list)]
        # temporarily fill it with changed IDs
        self.wizard_new_records_ids = [(6, 0, new_article_list)] #move this full list to after tag checking
        #for record in wizard_new_record_ids

        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Tag Checking', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('tag_extension.article_import_excel_wizard_form_view_tags').id, 'form')],  
            'target': 'current', }
        #Not sure if return will override super, but this will move part 2 to the tagging system
        #Make sure to create the new view listed here