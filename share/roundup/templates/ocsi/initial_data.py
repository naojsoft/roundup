#
# INITIALISE CLASS VALUES
#
category = db.getclass('category')
category.create(name="ocs", order="1")
category.create(name="sysadmin", order="2")
category.create(name="ocsbiz", order="3")
category.create(name="tcs", order="4")
category.create(name="ocsinbox", order="5")
category.create(name="tcsinbox", order="6")
category.create(name="ins", order="7")
category.create(name="insinbox", order="8")
category.create(name="ocsgen2", order="9")
category.create(name="subaru", order="10")
category.create(name="daycrew", order="11")
category.create(name="operators", order="12")

rank = db.getclass('rank')
rank.create(name="critical", order="1")
rank.create(name="urgent", order="2")
rank.create(name="high", order="3")
rank.create(name="medium", order="4")
rank.create(name="low", order="5")

importance = db.getclass('importance')
importance.create(name="urgent", order="1")
importance.create(name="high", order="2")
importance.create(name="medium", order="3")
importance.create(name="low", order="4")

stat = db.getclass('status')
stat.create(name="new", order="1")
stat.create(name="open", order="2")
stat.create(name="in-progress", order="3")
stat.create(name="testing", order="4")
stat.create(name="ready", order="5")
stat.create(name="watching", order="6")
stat.create(name="closed", order="7")
stat.create(name="deferred", order="8")

res = db.getclass('resolution')
res.create(name="resolved", order="1")
res.create(name="superceded", order="2")
res.create(name="not-applicable", order="3")
res.create(name="duplicate", order="4")
res.create(name="unresolved", order="5")

site = db.getclass('site')
site.create(name="summit", order="1")
site.create(name="remote-hilo", order="2")
site.create(name="remote-mitaka", order="3")
site.create(name="simulator", order="4")
site.create(name="other", order="5")

# Roles are records so that they can be administered from the web
# interface; schema.py registers each of these with the security system.
role = db.getclass('role')
role.create(name="User", description="Ordinary tracker user", order="1")
role.create(name="Uber",
            description="May administer groups, categories and permissions",
            order="2")
role.create(name="Lurker", description="May read issues but not change them",
            order="3")

# The property sets that a group may view and edit within a category.
_all_props = ("title,messages,files,nosy,creation,activity,creator,actor,"
              "keywords,site,importance,superseder,assignedto,status,"
              "resolved,categories,rank")
_client_view = ("title,messages,files,nosy,creation,activity,creator,actor,"
                "keywords,site,importance,superseder,assignedto,status,"
                "resolved,categories")
_client_edit = ("title,messages,files,nosy,creation,activity,creator,actor,"
                "keywords,site,importance")

permbundle = db.getclass('permbundle')
permbundle.create(name="Full", klass="issue",
                  viewprops=_all_props, editprops=_all_props)
permbundle.create(name="Client", klass="issue",
                  viewprops=_client_view, editprops=_client_edit)
permbundle.create(name="Lurker", klass="issue",
                  viewprops=_client_view, editprops="")

# Every user is implicitly a member of the group named "everyone";
# see lib/groupperm.py.
group = db.getclass('group')
group.create(name="everyone", description="All tracker users", order="1")

# create the two default users
user = db.getclass('user')
user.create(username="admin", password=adminpw,
            address=admin_email, roles='Admin')
user.create(username="anonymous", roles='Anonymous')

# vim: set filetype=python sts=4 sw=4 et si :
