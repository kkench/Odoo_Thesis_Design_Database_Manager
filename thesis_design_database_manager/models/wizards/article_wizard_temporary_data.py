from odoo import api,fields,models
import re

class ArticleWizardPublication(models.TransientModel):
    _name = "article.wizard.publication"
    _description = "Sample list of what will be uploaded"

    name = fields.Char("Title")
    course = fields.Selection([("T", "T"),("D", "D")],string="Course Code")
    initial_id = fields.Char("ID",compute="_compute_data_and_errors",readonly=True,store=True)
    uploader_email = fields.Char("Uploader Email", readonly=True)
    uploader_name = fields.Char("Uploader Name", readonly=True)
    # registration_date = fields.date("Date Registered")
    # last_edited = fields.date("Last Edited")
    abstract = fields.Text("Abstract")
    author1 = fields.Char("Author1", default=None)
    author2 = fields.Char("Author2", default=None)
    author3 = fields.Char("Author3", default=None)
    adviser = fields.Char("ADVISER")
    student_number_1 = fields.Char("Student Number 1", default=None)
    student_number_2 = fields.Char("Student Number 2", default=None)
    student_number_3 = fields.Char("Student Number 3", default=None)
    instructor_privilege_flag = fields.Boolean("Adviser Mode/Instructor (0/1)")# delete when you cant find a use case
    
    article_2_flag = fields.Boolean("Check if Article 2",default=False)
    article_to_update_id = fields.Many2one("article.publication","If Author has already existing ID",compute="_compute_data_and_errors",store=True)
    edit_binary_string = fields.Char("Editing Binary",default="0000")# Binary Boolean String; (1-If Complete Redefense; 2-Title Update; 3-Abstract Update; 4-Tag Update) 

    tags = fields.Text("TAGS")
    error_code = fields.Integer("Error Code Number", compute="_compute_data_and_errors", readonly=True, store=True)
    error_comment = fields.Char("Comments", compute="_compute_data_and_errors", readonly=True, store=True)

    import_wizard_id = fields.Many2one("article.import.excel.wizard")

    @api.depends('author1', 'author2', 'author3', 'uploader_email', 'tags','course', 'student_number_1', 'student_number_2', 'student_number_3', 'adviser','import_wizard_id')
    def _compute_data_and_errors(self):
        ''' Error Codes:
        0 - No Errors
        1 - Incorrect Name Format (Cannot Read) 
        2 - Student is not the editor
        3 - Invalid Course
        4 - Student Number Does Not Follow Proper Formatting
        5 - 3rd Author Exists on Thesis
        6 - Duplicate Submission
        7 - Tags Stuff
        8 - Cannot Search Adviser
        9 - Edit Mode, Record Not Searchable
        '''
        def reset_record(record):
            record.initial_id = None

        for record in self:
            record.error_comment = ""
            if not record.is_author_name_valid():
                record.error_code = 1
                record.error_comment = "One of the Author is not proper name format!"
                reset_record(record)
                continue             
            if not record.does_author_email_and_name_match(): 
                record.error_code = 2
                record.error_comment = "Uploader Error; Use Own Mapuan Email"
                reset_record(record)
                continue
            if record.course_is_unknown(): 
                record.error_code = 3
                record.error_comment = "No Course Given"
                reset_record(record)
                continue
            if not record.is_student_number_in_format():
                record.error_code = 4
                record.error_comment = "Student Number not Correct"
                reset_record(record)
                continue
            record.arrange_authors_alphabetically()
            record._update_initial_id()
            if record.course == "D" and (None in [record.author1,record.author2,record.author3]): # only max 2 authors for thesis
                record.error_code = 5
                record.error_comment = "2 Authors only for Thesis"
                reset_record(record)
                continue
            if record.record_has_duplicate_submission():
                record.error_code = 6
                record.error_comment = "Another Submission has been Made"
            if not record.tags_are_valid():
                record.error_code = 7
                record.error_comment = "Tagging Error"   
                reset_record(record)
                continue
            record._check_for_existing_records()
            if record.import_wizard_id.wizard_type == "new":
                if record._has_errors_for_new_articles(): #check if anything is wrong for new record
                    reset_record(record)
                    continue
                if record.article_to_update_id:
                    record.error_comment = "Existing Title Exists, Will Overwrite"
            if record.import_wizard_id.wizard_type == "edit":
                if record._has_errors_for_edit_articles():
                    reset_record(record)
                    continue
                record.link_existing_record()
            record.error_code = 0
            record.clear_newline_from_abstract_and_title()
        return

    ###FOR ERROR CHECKING (_compute_data_and_errors())
    def is_author_name_valid(self):
        #THIS IS A COMPUTE FUNCTION, DONT EDIT NON STORED RECORD DATA
        pattern_name = r'^[A-Z][a-z]+, ([A-Z][a-z]+ )+[A-Z]\.$'  # LN, FN MI
        if not (self.author1 or self.author2 or self.author3): return False
        for author_name in [self.author1, self.author2, self.author3]:
            if not author_name: continue
            if not re.match(pattern_name, author_name):
                return False
        return True

    def record_has_duplicate_submission(self):
        # Search for existing records with the same name and initial_id
        existing_temporary_data = self.env['article.wizard.publication'].search([
            ('initial_id', '=', self.initial_id),
            ('id', '!=', self.id if isinstance(self.id, int) else None),  # Exclude the current record   
            ('import_wizard_id', '=', self.import_wizard_id.id),
        ])
        if existing_temporary_data:
            return True
        return False

    def does_author_email_and_name_match(self):
        #THIS IS A COMPUTE FUNCTION, DONT EDIT NON STORED DATA
        pattern_mymail = r'^[a-zA-Z0-9._%+-]+@mymail\.mapua\.edu\.ph$'
        if not re.match(pattern_mymail, self.uploader_email):
            return False
        for author_name in [self.author1, self.author2, self.author3]:
            email_check = self.create_email_from_format(author_name) == self.uploader_email
            name_check = self.create_name_from_format_of_author(author_name) == self.uploader_name
            if email_check and name_check:
                return True
        return False #did not match any

    def create_email_from_format(self,name):
        if not isinstance(name, str): return "error"
        last_name, first_name_middle_initial = name.split(', ')
        first_names, middle_initial = first_name_middle_initial.rsplit(' ', 1)
        email = f"{''.join([name[0].lower() for name in first_names.split()])}{middle_initial[0].lower()}{last_name.lower()}@mymail.mapua.edu.ph"
        return email
    
    def create_name_from_format_of_author(self,name):
        if not isinstance(name, str): return "error"
        upper_name = name.upper()
        last_name, first_name_middle_initial = upper_name.split(', ')
        first_names, _ = first_name_middle_initial.rsplit(' ', 1)
        return first_names + " " + last_name
    
    def adviser_is_searchable(self):
        #THIS IS A COMPUTE FUNCTION, DONT EDIT NON STORED DATA
        if not self.adviser:return False
        # print(self.adviser.split(';'))
        for adviser_name in self.adviser.split(';'):
            adviser = self.env['res.users'].search([('name', '=', adviser_name)], limit=1)
            if adviser:
                if adviser.has_group('thesis_design_database_manager.group_article_faculty_adviser'):
                    continue
                else:
                    return False
        return True    
            
    def is_student_number_in_format(self):
        # THIS IS A COMPUTE FUNCTION, DON'T EDIT NON-STORED DATA
        student_list = [self.author1, self.author2, self.author3]
        student_number_list = [self.student_number_1, self.student_number_2, self.student_number_3]
        pattern = r'^20\d{2}\d{6}$'
        
        for student,student_number in zip(student_list,student_number_list):
            if student_number and not re.match(pattern, student_number):
                return False
            if student and not student_number:
                return False
        
        return not all(student_number is None for student_number in student_number_list)

    def course_is_unknown(self):
        return not (self.course in ['T','D'])

    def _has_errors_for_new_articles(self):
        #the function that calls this will cycle the records already, keep it as 'self' 
        #THIS IS A COMPUTE FUNCTION, DONT EDIT NON STORED DATA
        if not self.adviser_is_searchable():
            self.error_code = 8
            self.error_comment = "Adviser is Not Found"
            return True
        return False
    
    def _has_errors_for_edit_articles(self):
        #self is already a single instance
        #this assumes wizard is on edit mode
        if not self.article_to_update_id:
            self.error_code = 9
            self.error_comment = "Cannot Find Existing Record"
            self.article_to_update_id = None
            return True
        if self.import_wizard_id.user_privilege != "faculty_adviser": return False

        for adviser in self.article_to_update_id.adviser_ids:
            if adviser.name in self.adviser.split(";"):
                return False
        self.error_code = 10
        self.error_comment = "User is not an adviser"
        return True

    def _check_for_existing_records(self):
        if not self.initial_id: return False
        existing_record_article = self.env['article.publication'].search([('custom_id', '=', self.initial_id)], limit=1)
        if existing_record_article: #not an error but will allocate updates to the old data
            self.article_to_update_id = existing_record_article.id
            return True
        else:
            self.article_to_update_id = None
            return False
    ##########################

    def _update_initial_id(self):
        for record in self:
            #--------------GET THE LAST NAMES IN ORDER----------------------
            record.initial_id = record.author1.split(', ')[0] #last name
            record.initial_id += record.author2.split(', ')[0] if self.author2 else ""
            record.initial_id += record.author3.split(', ')[0] if record.author3 else ""
            #-------------------------------------------------------------
            #-------------Get latest student Number as year----------------
            #student number is not perfect representation of the year of the student as shs sn exists
            latest_student_number = int(record.student_number_1[0:4]) if isinstance(record.student_number_1, str) else None
            for student_number in [record.student_number_2,record.student_number_3,]:
                if not student_number:break
                current_yr = int(student_number[0:4])
                latest_student_number = current_yr if latest_student_number<current_yr else latest_student_number

            record.initial_id += "_" + str(latest_student_number)
            #---------------------------------------------------------
            #-------------Include Course Initial------------------
            record.initial_id += "_" + record.course
            #-------------For Thesis Articles-----------------------
            if record.course == "T":
                record.initial_id += "_Art2" if record.article_2_flag else "_Art1"

    def arrange_authors_alphabetically(self):
        # print("arranging now")
        # Collect author names and filter out None values
        # if not self.is_student_number_in_format(): return

        author_student_number = {
            self.author1: self.student_number_1,
            self.author2: self.student_number_2,
            self.author3: self.student_number_3,
        }
        author_names = [name for name in [self.author1, self.author2, self.author3] if name]
        
        # Sort the names alphabetically
        sorted_names = sorted(author_names)
        # Fill with None to ensure the list has 3 elements
        sorted_names.extend([None] * (3 - len(sorted_names)))
        sorted_student_number = [author_student_number[author_name] if author_name else None for author_name in sorted_names]
        if sorted_names == [self.author1, self.author2, self.author3]:
            return True
        else:
            self.author1, self.author2, self.author3 = sorted_names
            self.student_number_1, self.student_number_2, self.student_number_3 = sorted_student_number
            return False

    def clear_newline_from_abstract_and_title(self):
        for record in self:
            if not record.abstract: continue
            abstract = record.abstract 
            abstract = re.sub(r'\n+', ' ', abstract)
            abstract = re.sub(r'\s{2,}', ' ', abstract)
            record.abstract = abstract
            
            title = record.name
            title = re.sub(r'\n+', ' ', title)
            title = re.sub(r'\s{2,}', ' ', title)
            record.name = title
            
    def tags_are_valid(self):
        #THIS IS A COMPUTE FUNCTION, DONT EDIT NON STORED DATA
        return True
    
    def act_open_error_code(self):
        self.ensure_one()
        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Error', 
            'view_mode': 'form', 
            'res_model': 'article.wizard.publication',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.view_article_wizard_publication_error_code_popup').id, 'form')], 
            'target': 'new', }
    
    def link_existing_record(self):
        # print("another one bites the dust")
        binary_string = self.edit_binary_string
        # print(binary_string)
        if binary_string == "0000" or not binary_string:
            return False
        if not self.article_to_update_id:
            return False
        if int(binary_string[0]):  # Edit everything
            return True
        else:
            print(bool(int(binary_string[1])),bool(int(binary_string[2])),bool(int(binary_string[3])))
            # self.adviser = self.article_to_update_id.adviser_ids
            semicolon_separated_advisers = "" 
            for adviser_id in self.article_to_update_id.adviser_ids:
                semicolon_separated_advisers += adviser_id.name if semicolon_separated_advisers == "" else f";{adviser_id.name}"
            self.adviser = semicolon_separated_advisers
            if not int(binary_string[1]):  # If not supposed to edit, copy it
                print("title checked")
                self.name = self.article_to_update_id.name
            if not int(binary_string[2]):
                print("abstract checked")
                self.abstract = self.article_to_update_id.abstract
            if int(binary_string[3]):
                pass  
        return True

    #################
