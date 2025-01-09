from odoo import api,fields,models
import nltk

class ArticlePublication(models.Model):
    _inherit = "article.publication"
    
    def act_suggested_tags(self):
        if self.name:
            all_tags = self.env['article.tag'].search([])
            tag_names = nltk.word_tokenize(self.name)
            
            for word, pos in ntlk.pos_tag(tag_names):
                   if pos == "IN":
                        continue
                   else:
                        suggested_tags.append(word)

            suggested_tags = self.env['article.tag'].search([
                ('name', 'in', found_tags),
                ("id","not in", self.article_tag_ids.ids) #all tags in found tags and not currently assigned to this model
                ])
            existing_tags = self.env['article.tag'].search([
                ("id","in",self.article_tag_ids.ids) #all tags currently assigned to this model
            ])
            
            combined_tags = (suggested_tags)|(existing_tags)
            self.article_tag_ids = [(6,0, combined_tags.ids)]

        return #doesn't work yet cause the nltk database isn't downloaded yet