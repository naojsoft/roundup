import groupperm as gpm

#
# TRACKER SCHEMA
#

# Class automatically gets these properties:
#   creation = Date()
#   activity = Date()
#   creator = Link('user')
#   actor = Link('user')

rank = Class(db, "rank",
                name=String(), order=Number())
rank.setkey("name")

importance = Class(db, "importance",
                name=String(), order=Number())
importance.setkey("name")

# Statuses
stat = Class(db, "status",
                name=String(),
                order=Number())
stat.setkey("name")

res = Class(db, "resolution",
                name=String(), order=Number())
res.setkey("name")

site = Class(db, "site",
                name=String(), order=Number())
site.setkey("name")

keyword = Class(db, "keyword",
                name=String(), categories=Multilink("category"),
                description=String())
keyword.setkey("name")

# Issues are partitioned into categories; see lib/groupperm.py.
category = Class(db, "category",
                 name=String(),
                 description=String(),
                 order=Number())
category.setkey("name")

# User-defined saved searches
query = Class(db, "query",
                klass=String(),
                name=String(),
                url=String(),
                private_for=Link('user'))

role = Class(db, "role",
             name=String(),
             description=String(),
             order=Number())
role.setkey("name")

catrole = Class(db, "catrole",
                catid=Link("category"),
                roleid=Link("role"))

group = Class(db, "group",
              name=String(),
              description=String(),
              members=Multilink("user"),
              order=Number())
group.setkey("name")

# A named set of issue properties that may be viewed and/or edited.
permbundle = Class(db, "permbundle",
                   name=String(),
                   klass=String(),
                   klassperms=String(),
                   viewprops=String(),
                   editprops=String())
permbundle.setkey("name")

# Grants a group one permission bundle within one category.
groupperm = Class(db, "groupperm",
                  grpid=Link("group"),
                  catid=Link("category"),
                  permid=Link("permbundle"),
                  comment=String())

user = Class(db, "user",
                username=String(),
                password=Password(),
                address=String(),
                realname=String(),
                phone=String(),
                organisation=String(),
                alternate_addresses=String(),
                queries=Multilink('query'),
                roles=String(),     # comma-separated string of Role names
                timezone=String())
user.setkey("username")
db.security.addPermission(name='Register', klass='user',
                          description='User is allowed to register new user')

# FileClass automatically gets this property in addition to the Class ones:
#   content = String()    [saved to disk in <tracker home>/db/files/]
#   type = String()       [MIME type of the content, default 'text/plain']
msg = FileClass(db, "msg",
                author=Link("user", do_journal='no'),
                recipients=Multilink("user", do_journal='no'),
                date=Date(),
                summary=String(),
                files=Multilink("file"),
                messageid=String(),
                inreplyto=String())

file = FileClass(db, "file",
                name=String())

# IssueClass automatically gets these properties in addition to the Class ones:
#   title = String()
#   messages = Multilink("msg")
#   files = Multilink("file")
#   nosy = Multilink("user")
#   superseder = Multilink("issue")
issue = IssueClass(db, "issue",
                   assignedto=Multilink("user"),
                   categories=Multilink("category"),
                   keywords=Multilink("keyword"),
                   rank=Link("rank"),
                   status=Link("status"),
                   importance=Link("importance"),
                   site=Multilink("site"),
                   resolved=Link("resolution"))

#
# TRACKER SECURITY SETTINGS
#
# See the configuration and customisation document for information
# about security setup.

# Roles are held as records so that they can be administered from the
# web interface; register each with the security system.
# Only read the table when the database says it exists. During
# "roundup-admin initialise" schema.py runs before the tables are
# created, and on PostgreSQL a failed query aborts the entire
# transaction, taking the rest of the table creation down with it --
# catching the Python exception is not enough.
_roles = []
if 'role' in (getattr(db, 'database_schema', None) or {}).get('tables', {}):
    _roles = [db.getnode('role', roleid) for roleid in db.role.list()]
for _node in _roles:
    db.security.addRole(name=_node['name'], description=_node['description'])

# The roles this schema grants permissions to must exist even when the
# role class has not been populated yet -- during "roundup-admin
# initialise", schema.py runs before initial_data.py.  Role names are
# held lowercased by the security system.
for _name, _description in (
        ('Uber', 'May administer groups, categories and permissions'),
        ('Lurker', 'May read issues but not change them'),
):
    if _name.lower() not in db.security.role:
        db.security.addRole(name=_name, description=_description)

#
# REGULAR USERS
#
# Give the regular users access to the web and email interface
db.security.addPermissionToRole('User', 'Web Access')
db.security.addPermissionToRole('User', 'Email Access')
db.security.addPermissionToRole('Uber', 'Web Roles')

for cl in ['query']:
    db.security.addPermissionToRole('User', 'View', cl)
    db.security.addPermissionToRole('User', 'Edit', cl)
    db.security.addPermissionToRole('User', 'Create', cl)
for cl in ['file', 'msg']:
    db.security.addPermissionToRole('User', 'View', cl)
    db.security.addPermissionToRole('User', 'Edit', cl)
    db.security.addPermissionToRole('User', 'Create', cl)
# Issue access is not granted here; it is derived from the issue's
# categories farther below.
for cl in ['status', 'resolution', 'importance', 'site', 'rank']:
    db.security.addPermissionToRole('User', 'View', cl)
for cl in ['keyword']:
    db.security.addPermissionToRole('User', 'View', cl)
for cl in ['group', 'permbundle', 'groupperm', 'category', 'keyword', 'user']:
    db.security.addPermissionToRole('Uber', 'View', cl)
    db.security.addPermissionToRole('Uber', 'Edit', cl)
    db.security.addPermissionToRole('Uber', 'Create', cl)

# May users view other user information? Comment these lines out
# if you don't want them to
p = db.security.addPermission(name='View', klass='user',
    properties=('id', 'organisation', 'phone', 'realname', 'timezone',
    'username'))
db.security.addPermissionToRole('User', p)


# Users should be able to edit their own details -- this permission is
# limited to only the situation where the Viewed or Edited item is their own.
def own_record(db, userid, itemid):
    '''Determine whether the userid matches the item being accessed.'''
    return userid == itemid


p = db.security.addPermission(name='View', klass='user', check=own_record,
    description="User is allowed to view their own user details")
db.security.addPermissionToRole('User', p)
p = db.security.addPermission(name='Edit', klass='user', check=own_record,
    properties=('username', 'password', 'address', 'realname', 'phone',
                'organisation', 'alternate_addresses', 'queries', 'timezone'),
    description="User is allowed to edit their own user details")
db.security.addPermissionToRole('User', p)

# Users should be able to edit and view their own queries. They should also
# be able to retire them.
def edit_query(db, userid, itemid):
    '''Determine whether the userid matches the item being accessed.'''
    return userid == db.query.get(itemid, 'creator')


p = db.security.addPermission(name='View', klass='query', check=edit_query,
    description="User is allowed to view their own queries")
db.security.addPermissionToRole('User', p)
p = db.security.addPermission(name='Edit', klass='query', check=edit_query,
    description="User is allowed to edit their own queries")
db.security.addPermissionToRole('User', p)
p = db.security.addPermission(name='Retire', klass='query', check=edit_query,
    description="User is allowed to retire their own queries")
db.security.addPermissionToRole('User', p)
p = db.security.addPermission(name='Create', klass='query',
    description="User is allowed to create queries")
db.security.addPermissionToRole('User', p)


####### ISSUE VIEW/EDIT/CREATE PERMISSIONS #######
#
# Every issue property gets a permission whose check consults the user's
# group memberships in the issue's categories (see lib/groupperm.py).
#
# Each check is paired with an equivalent filter.  Roundup uses the filter
# to express the same restriction as a database query, so that listing and
# searching issues does not have to run the Python check over every issue
# in the tracker.  The two must always be kept in step.
for propname in db.issue.getprops():

    perm = db.security.addPermission(name='View', klass='issue',
         properties=[propname],
         check=gpm.make_check(propname, gpm.VIEW),
         filter=gpm.make_filter(propname, gpm.VIEW),
         description='User may view this issue property in categories '
                     'their groups give them view access to')
    db.security.addPermissionToRole('User', perm)

    perm = db.security.addPermission(name='Edit', klass='issue',
         properties=[propname],
         check=gpm.make_check(propname, gpm.EDIT),
         filter=gpm.make_filter(propname, gpm.EDIT),
         description='User may edit this issue property in categories '
                     'their groups give them edit access to')
    db.security.addPermissionToRole('User', perm)

    # permbundle has no separate "creatable" property set; Create has
    # always been granted on the strength of the edit set.
    perm = db.security.addPermission(name='Create', klass='issue',
         properties=[propname],
         check=gpm.make_check(propname, gpm.EDIT),
         filter=gpm.make_filter(propname, gpm.EDIT),
         description='User may set this issue property when creating an '
                     'issue in categories their groups give them edit '
                     'access to')
    db.security.addPermissionToRole('User', perm)

    # Search permissions carry no check: a permission with a check is not
    # searchable, and Roundup *silently drops* search and sort criteria on
    # properties a user cannot search, which would give wrong results
    # rather than an error.  Which issues come back is still governed by
    # the View permissions above, so this does not widen what a user can
    # read.  Roundup 1.4.11 had no search-permission concept at all, so
    # granting these preserves the tracker's existing behaviour.
    perm = db.security.addPermission(name='Search', klass='issue',
         properties=[propname],
         description='User may search and sort on this issue property')
    db.security.addPermissionToRole('User', perm)

# Filtering issues by category requires the category class to be
# searchable on the properties Roundup uses to resolve a link: the id,
# the key property and the order property.
perm = db.security.addPermission(name='Search', klass='category',
    properties=('id', 'name', 'order'),
    description='User may filter and sort issues by category')
db.security.addPermissionToRole('User', perm)

#
# ANONYMOUS USER PERMISSIONS
#
# Let anonymous users access the web interface. Note that almost all
# trackers will need this Permission. The only situation where it's not
# required is in a tracker that uses an HTTP Basic Authenticated front-end.
db.security.addPermissionToRole('Anonymous', 'Web Access')

# Let anonymous users access the email interface (note that this implies
# that they will be registered automatically, hence they will need the
# "Create" user Permission below)
# This is disabled by default to stop spam from auto-registering users on
# public trackers.
#db.security.addPermissionToRole('Anonymous', 'Email Access')

# Assign the appropriate permissions to the anonymous user's Anonymous
# Role. Choices here are:
# - Allow anonymous users to register
db.security.addPermissionToRole('Anonymous', 'Register', 'user')

# Allow anonymous users access to view issues (and the related, linked
# information).
#for cl in 'issue', 'file', 'msg', 'keyword', 'priority', 'status':
#    db.security.addPermissionToRole('Anonymous', 'View', cl)

# [OPTIONAL]
# Allow anonymous users access to edit the "issue" class of data
# Note: this also grants access to create related information like
#       files and messages etc that are linked to issues
#db.security.addPermissionToRole('Anonymous', 'Edit', 'issue')
#db.security.addPermissionToRole('Anonymous', 'Create', 'issue')


# vim: set filetype=python sts=4 sw=4 et si :
