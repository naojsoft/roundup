"""Category-based permissions for the Subaru OCS issue tracker.

Issues belong to one or more categories (the ``categories`` Multilink on
``issue``).  What a user may see and edit is decided per category::

    user      -> groups        via group.members
    group     -> category      via groupperm.grpid / groupperm.catid
    groupperm -> permbundle    via groupperm.permid
    permbundle-> property sets  permbundle.viewprops / permbundle.editprops

A user may view (or edit) a property of an issue if *any* of that issue's
categories grants them that property.  The group named ``everyone``
implicitly contains every user.

Two entry points are handed to Roundup's security system for each issue
property, and they must agree:

``make_check(prop, bit)``
    Row-at-a-time test, used when Roundup holds a single item id.

``make_filter(prop, bit)``
    The same restriction expressed as a filterspec, so that listing and
    searching can push it into SQL instead of testing every candidate row
    in Python.  Without this, Roundup falls back to the per-row check for
    every issue in the tracker on every index page.

Note that the permission map is rebuilt whenever Roundup clears its node
cache -- that is, at every commit or rollback, so at least once per
request.  This matters because in optimised (production) mode a single
Database object is reused across requests and ``schema.py`` runs only at
startup; caching the map for the process lifetime would leave permission
edits with no effect until the tracker was restarted.
"""

# Permission bits.  Note that "create" deliberately reuses the edit bit:
# permbundle has no separate set of creatable properties, and the tracker
# has always granted Create on the strength of editprops.
VIEW = 0x1
EDIT = 0x2

_CACHE_ATTR = '_ocsi_policy'
_HOOK_ATTR = '_ocsi_policy_hooked'


class _Policy(object):
    """Resolved (user, category, property) -> permission bits."""

    __slots__ = ('mask', 'user_cats')

    def __init__(self):
        # (userid, catid, propname) -> bits.  propname None means
        # "any access at all in this category", used to decide which
        # categories a user may see.
        self.mask = {}
        # userid -> set of catids the user has any access to
        self.user_cats = {}

    def grant(self, userids, catid, propnames, bits):
        mask = self.mask
        cats = self.user_cats
        for propname in propnames:
            for userid in userids:
                key = (userid, catid, propname)
                mask[key] = mask.get(key, 0) | bits
                key = (userid, catid, None)
                mask[key] = mask.get(key, 0) | bits
                cats.setdefault(userid, set()).add(catid)

    def allows(self, userid, catid, propname, bits):
        return bool(self.mask.get((userid, catid, propname), 0) & bits)


def _split_props(value):
    """permbundle stores property sets as a comma separated string."""
    if not value:
        return []
    return [p.strip() for p in value.split(',') if p.strip()]


def _build(db):
    policy = _Policy()
    everyone = None
    for permid in db.groupperm.list():
        gp = db.getnode('groupperm', permid)
        catid = gp['catid']
        if not catid or not gp['grpid'] or not gp['permid']:
            # Incomplete record; nothing sensible to grant.
            continue

        group = db.getnode('group', gp['grpid'])
        members = group['members'] or []
        if group['name'] == 'everyone':
            if everyone is None:
                everyone = db.user.list()
            members = everyone
        if not members:
            continue

        bundle = db.getnode('permbundle', gp['permid'])
        policy.grant(members, catid, _split_props(bundle['viewprops']), VIEW)
        policy.grant(members, catid, _split_props(bundle['editprops']),
                     VIEW | EDIT)
    return policy


def _forget(db):
    setattr(db, _CACHE_ATTR, None)


def policy(db):
    """The permission map for this database, rebuilt once per transaction."""
    current = getattr(db, _CACHE_ATTR, None)
    if current is None:
        current = _build(db)
        setattr(db, _CACHE_ATTR, current)
        if not getattr(db, _HOOK_ATTR, False):
            # Roundup calls this at the end of every commit and rollback.
            db.registerClearCacheCallback(_forget, db)
            setattr(db, _HOOK_ATTR, True)
    return current


def issue_categories(db, itemid):
    try:
        return db.issue.get(itemid, 'categories') or []
    except (IndexError, KeyError):
        # Item has gone away, or has no categories property.
        return []


def categories_for(db, userid, propname, bits):
    """Categories in which this user holds `bits` on `propname`."""
    pol = policy(db)
    return [catid for catid in pol.user_cats.get(userid, ())
            if pol.allows(userid, catid, propname, bits)]


def make_check(propname, bits):
    """Build a Roundup permission check for one issue property."""

    def check(db, userid, itemid):
        if itemid is None or itemid == '':
            # A class-level test; Roundup only calls check() with an item.
            return False
        pol = policy(db)
        for catid in issue_categories(db, itemid):
            if pol.allows(userid, catid, propname, bits):
                return True
        return False

    return check


def make_filter(propname, bits):
    """The same restriction as make_check, pushed into the database.

    Roundup calls this with (db, userid, class) and expects a list of
    keyword argument dicts for Class.filter(); an item is permitted if it
    matches any of them.  An empty list means "nothing is permitted",
    which is what we want for a user with no categories.
    """

    def filter(db, userid, cls):
        catids = categories_for(db, userid, propname, bits)
        if not catids:
            return []
        return [{'filterspec': {'categories': catids}}]

    return filter


def user_category_ids(db, userid):
    """Every category this user has any access to, in tracker order."""
    pol = policy(db)
    allowed = pol.user_cats.get(userid, set())
    return [catid for catid in db.category.list() if catid in allowed]


def default_category(db):
    """The category shown to users who have not chosen one."""
    try:
        return db.category.lookup('subaru')
    except KeyError:
        ids = db.category.list()
        return ids[0] if ids else None


# --- templating utilities -------------------------------------------------
#
# These back the category selector in page.html.  The selected category is
# a display preference held in a cookie; it deliberately has no bearing on
# what the permission checks above allow, which depends only on the issue's
# own categories and the user's group memberships.

class Category(object):
    """A category as the page templates want to see it."""

    def __init__(self, id, name):
        self.id = id
        self.name = name


def _is_anonymous(db, userid):
    try:
        return db.user.get(userid, 'username') == 'anonymous'
    except (IndexError, KeyError):
        return True


def getUserCategories(request):
    """The categories this user may choose between."""
    db = request.client.db
    userid = request.client.userid

    def node(catid):
        return Category(catid, db.getnode('category', catid)['name'])

    if not userid or _is_anonymous(db, userid):
        catid = default_category(db)
        return [node(catid)] if catid else []

    return [node(catid) for catid in user_category_ids(db, userid)]


def getCategory(request):
    """The current category, from the roundup_category cookie."""
    client = request.client
    db = client.db

    catid = None
    cookie = client.cookie.get('roundup_category')
    if cookie is not None:
        catid = cookie.value
        if not db.category.hasnode(catid) or db.category.is_retired(catid):
            client.add_error_message(
                "Unknown category %r; using the default instead." % catid)
            catid = None
        elif catid not in user_category_ids(db, client.userid):
            # Not a security boundary -- the permission checks above deny
            # the issues regardless -- but showing a category the user has
            # no access to would just yield an unexplained empty list.
            client.add_error_message(
                "You do not have access to category %r; using the default "
                "instead." % db.category.get(catid, 'name'))
            catid = None

    if catid is None:
        catid = default_category(db)
    return catid
