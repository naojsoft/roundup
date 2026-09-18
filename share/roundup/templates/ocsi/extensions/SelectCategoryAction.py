from urllib.parse import quote

from roundup.cgi import exceptions
from roundup.cgi.actions import Action

import groupperm as gpm


class SelectCategoryAction(Action):
    """Set the category the user is currently browsing.

    The chosen category is a display preference kept in a cookie.  It
    decides which issues the index page shows by default; it does not
    decide what the user is allowed to see, which depends only on the
    issue's own categories and the user's group memberships.
    """

    SUCCESS = ('%sissue?@ok_message=%s&@sort=-activity&@group=status'
               '&@filter=categories,status'
               '&@columns=id,activity,creator,title,assignedto'
               '&status=-1,1,2,3,4,5&categories=%s')
    FAILURE = '%s?@error_message=%s'

    def fail(self, message):
        raise exceptions.Redirect(self.FAILURE % (self.base, quote(message)))

    def handle(self):
        categories = self.db.getclass('category')

        if '__category' in self.form:
            name = self.form['__category'].value
            try:
                catid = categories.lookup(name)
            except KeyError:
                self.fail('No category found matching name "%s"' % name)
        else:
            # Default to the first category this user can reach.
            allowed = gpm.user_category_ids(self.db, self.userid)
            catid = allowed[0] if allowed else gpm.default_category(self.db)
            if catid is None:
                self.fail('No categories are defined in this tracker')
            name = categories.get(catid, 'name')

        if catid not in gpm.user_category_ids(self.db, self.userid):
            self.fail("Sorry, you don't have permission to access that "
                      "category")

        # Save the category, then redirect so the new cookie is sent.
        self.client.add_cookie('roundup_category', catid)
        raise exceptions.Redirect(self.SUCCESS % (
            self.base, quote('Category changed to %s' % name), quote(catid)))


def init(instance):
    instance.registerAction('selectcategory', SelectCategoryAction)
