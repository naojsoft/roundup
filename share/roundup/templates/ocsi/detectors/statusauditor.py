# Copyright (c) 2002 ekit.com Inc (http://www.ekit-inc.com/)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# This is the classic template's statusauditor adapted to the OCSI
# schema.
#
# The stock version defaulted a new issue to the status "unread" and
# moved quiescent issues to "chatting" when a message arrived. Neither
# status exists here -- OCSI uses new, open, in-progress, testing, ready,
# watching, closed and deferred -- so both lookups raised KeyError and
# both handlers returned silently. The effect was that issues created
# without an explicit status kept no status at all.
#
# The "chatting" auto-transition is deliberately not reimplemented: it
# has never fired on this tracker, and giving it an OCSI equivalent would
# start silently changing the status of any issue that receives a
# message. That is a policy decision, not a port.

DEFAULT_STATUS = 'new'


def preset_status(db, cl, nodeid, newvalues):
    """Give a new issue a status when none was supplied."""
    if newvalues.get('status'):
        return

    try:
        newvalues['status'] = db.status.lookup(DEFAULT_STATUS)
    except KeyError:
        # The status does not exist; leave the issue alone rather than
        # failing the create.
        return


def init(db):
    db.issue.audit('create', preset_status)

# vim: set filetype=python ts=4 sw=4 et si
