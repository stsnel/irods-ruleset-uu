# -*- coding: utf-8 -*-
"""Functions to act on user-visible folders in the research or vault area."""

__copyright__ = 'Copyright (c) 2019-2020, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import epic
import group
import irods_types
import meta
import policies_folder_status
import provenance
import vault
from util import *
from util.query import Query


__all__ = ['rule_collection_group_name',
           'api_folder_get_locks',
           'api_folder_lock',
           'api_folder_unlock',
           'api_folder_submit',
           'api_folder_unsubmit',
           'api_folder_accept',
           'api_folder_reject',
           'rule_folder_secure']


def set_status(ctx, coll, status):
    """Change a folder's status.

    Status changes are validated by policy (AVU modify preproc).
    """
    # Ideally we would pass in the current (expected) status as part of the
    # request, and perform a metadata 'mod' operation instead of a 'set'.
    # However no such msi exists.
    # With 'mod' we can be sure that we are performing the correct state
    # transition. Otherwise the original status in a transition can be
    # different from the expected current status, resulting in e.g. a validated
    # SECURED -> FOLDER transition, while the request was for a REJECTED ->
    # FOLDER transition.
    try:
        if status.value == '':
            avu.rmw_from_coll(ctx, coll, constants.IISTATUSATTRNAME, '%')
        else:
            avu.set_on_coll(ctx, coll, constants.IISTATUSATTRNAME, status.value)
    except Exception as e:
        x = policies_folder_status.can_set_folder_status_attr(ctx,
                                                              user.user_and_zone(ctx),
                                                              coll,
                                                              status.value)
        if x:
            return api.Error('internal', 'Could not update folder status due to an internal error', str(e))
        else:
            return api.Error('not_allowed', x.reason)
    return api.Result.ok()


def set_status_as_datamanager(ctx, coll, status):
    """Change a folder's status as a datamanager."""
    res = ctx.iiFolderDatamanagerAction(coll, status.value, '', '')
    if res['arguments'][2] != 'Success':
        return api.Error(*res['arguments'][1:])


@api.make()
def api_folder_lock(ctx, coll):
    """Lock a folder.

    :param coll: Folder to lock
    """
    return set_status(ctx, coll, constants.research_package_state.LOCKED)


@api.make()
def api_folder_unlock(ctx, coll):
    """Unlock a folder.

    Unlocking is implemented by clearing the folder status. Since this action
    can also represent other state changes than "unlock", we perform a sanity
    check to see if the folder is currently in the expected state.

    :param coll: Folder to unlock
    """
    if get_status(ctx, coll) is not constants.research_package_state.LOCKED:
        return api.Error('status_changed',
                         'Insufficient permissions or the folder is currently not locked')

    return set_status(ctx, coll, constants.research_package_state.FOLDER)


@api.make()
def api_folder_submit(ctx, coll):
    """Submit a folder.

    :param coll: Folder to submit
    """
    return set_status(ctx, coll, constants.research_package_state.SUBMITTED)


@api.make()
def api_folder_unsubmit(ctx, coll):
    """Unsubmit a folder.

    :param coll: Folder to unsubmit
    """
    # Sanity check. See 'unlock'.
    if get_status(ctx, coll) is not constants.research_package_state.SUBMITTED:
        return api.Error('status_changed', 'Folder cannot be unsubmitted because its status has changed.')

    return set_status(ctx, coll, constants.research_package_state.FOLDER)


@api.make()
def api_folder_accept(ctx, coll):
    """Accept a folder.

    :param coll: Folder to accept
    """
    return set_status_as_datamanager(ctx, coll, constants.research_package_state.ACCEPTED)


@api.make()
def api_folder_reject(ctx, coll):
    """Reject a folder.

    :param coll: Folder to reject
    """
    return set_status_as_datamanager(ctx, coll, constants.research_package_state.REJECTED)


@rule.make(inputs=[0], outputs=[1])
def rule_folder_secure(ctx, coll):
    """Rule entry to folder_secure: Secure a folder to the vault.
    This function should only be called by a rodsadmin
    and should not be called from the portal.

    :param coll: Folder to secure

    :return: '0' when nu error occurred
    """
    log.write(ctx, 'Starting folder secure - ' + coll)

    return folder_secure(ctx, coll)


def folder_secure(ctx, coll):
    """Secure a folder to the vault.
    This function should only be called by a rodsadmin
    and should not be called from the portal.

    :param coll: Folder to secure

    :return: '0' when nu error occurred
    """
    if user.user_type(ctx) != 'rodsadmin':
        log.write(ctx, "User is no rodsadmin")
        return '1'

    # Check modify access on research folder.
    msi.check_access(ctx, coll, 'modify object', irods_types.BytesBuf())

    modify_access = msi.check_access(ctx, coll, 'modify object', irods_types.BytesBuf())['arguments'][2]

    # Set cronjob status
    if modify_access != b'\x01':
        try:
            msi.set_acl(ctx, "default", "admin:write", user.full_name(ctx), coll)
        except msi.Error as e:
            log.write(ctx, "Could not set acl (admin:write) for collection: " + coll)
            return '1'

    avu.set_on_coll(ctx, coll, constants.UUORGMETADATAPREFIX + "cronjob_copy_to_vault", constants.CRONJOB_STATE['PROCESSING'])

    found = False
    iter = genquery.row_iterator(
        "META_COLL_ATTR_VALUE",
        "COLL_NAME = '" + coll + "' AND META_COLL_ATTR_NAME = '" + constants.IICOPYPARAMSNAME + "'",
        genquery.AS_LIST, ctx
    )
    for row in iter:
        target = row[0]
        found = True

    if found:
        avu.rm_from_coll(ctx, coll, constants.IICOPYPARAMSNAME, target)

    if modify_access != b'\x01':
        try:
            msi.set_acl(ctx, "default", "admin:null", user.full_name(ctx), coll)
        except msi.Error as e:
            log.write(ctx, "Could not set acl (admin:null) for collection: " + coll)
            return '1'

    if not found:
        target = determine_vault_target(ctx, coll)
        if target == "":
            log.write(ctx, "No vault target found")
            return '1'

    # Try to register EPIC PID
    ret = epic.register_epic_pid(ctx, target)
    url = ret['url']
    pid = ret['pid']
    http_code = ret['httpCode']

    if (http_code != "0" and http_code != "200" and http_code != "201"):
        # Always retry
        log.write(ctx, "folder_secure:  returned httpCode: " + http_code)
        if modify_access != b'\x01':
            try:
                msi.set_acl(ctx, "default", "admin:write", user.full_name(ctx), coll)
            except msi.Error as e:
                return '1'

        avu.set_on_coll(ctx, coll, constants.UUORGMETADATAPREFIX + "cronjob_copy_to_vault", constants.CRONJOB_STATE['RETRY'])
        avu.set_on_coll(ctx, coll, constants.IICOPYPARAMSNAME, target)

        if modify_access != b'\x01':
            try:
                msi.set_acl(ctx, "default", "admin:null", user.full_name(ctx), coll)
            except msi.Error as e:
                log.write(ctx, "Could not set acl (admin:null) for collection: " + coll)
                return '1'

    # Copy all original info to vault
    vault.copy_folder_to_vault(ctx, coll, target)
    meta.copy_user_metadata(ctx, coll, target)
    vault.vault_copy_original_metadata_to_vault(ctx, target)
    vault.vault_write_license(ctx, target)

    if http_code != "0":
        # save EPIC Persistent ID in metadata
        epic.save_epic_pid(ctx, target, url, pid)

    # Set research folder status.
    try:
        msi.set_acl(ctx, "recursive", "admin:write", user.full_name(ctx), coll)
    except msi.Error as e:
        log.write(ctx, "Could not set acl (admin:write) for collection: " + coll)
        return '1'

    parent, chopped_coll = pathutil.chop(coll)

    while parent != "/" + user.zone(ctx) + "/home":
        log.write(ctx, parent)
        try:
            msi.set_acl(ctx, "default", "admin:write", user.full_name(ctx), parent)
            log.write(ctx, "SET ACL (admin:write) on " + parent)
        except msi.Error as e:
            log.write(ctx, "Could not set ACL on " + parent)
        parent, chopped_coll = pathutil.chop(parent)

    avu.set_on_coll(ctx, coll, constants.IISTATUSATTRNAME, constants.research_package_state.SECURED)

    try:
        msi.set_acl(ctx, "recursive", "admin:null", user.full_name(ctx), coll)
    except msi.Error as e:
        log.write(ctx, "Could not set acl (admin:null) for collection: " + coll)
        return '1'

    parent, chopped_coll = pathutil.chop(coll)
    while parent != "/" + user.zone(ctx) + "/home":
        try:
            msi.set_acl(ctx, "default", "admin:null", user.full_name(ctx), parent)
        except msi.Error as e:
            log.write(ctx, "Could not set ACL (admin:null) on " + parent)

        parent, chopped_coll = pathutil.chop(parent)

    # Copy provenance log.
    provenance.provenance_copy_log(ctx, coll, target)

    # Set vault permissions for new vault package.
    group = collection_group_name(ctx, coll)
    if group == '':
        log.write(ctx, "Cannot determine which research group " + coll + " belongs to")
        return '1'

    vault.set_vault_permissions(ctx, group, coll, target)

    # Set vault package status.
    log.write(ctx, "BEFORE set vault package status to unpublished")
    avu.set_on_coll(ctx, target, constants.IIVAULTSTATUSATTRNAME, constants.vault_package_state.UNPUBLISHED)
    log.write(ctx, "After set vault package status to unpublished")

    # Set cronjob status.
    if modify_access != b'\x01':
        try:
            msi.set_acl(ctx, "default", "admin:write", user.full_name(ctx), coll)
        except msi.Error as e:
            log.write(ctx, "Could not set acl (admin:write) for collection: " + coll)
            return '1'

    avu.set_on_coll(ctx, coll, constants.UUORGMETADATAPREFIX + "cronjob_copy_to_vault", constants.CRONJOB_STATE['OK'])

    if modify_access != b'\x01':
        try:
            msi.set_acl(ctx, "default", "admin:null", user.full_name(ctx), coll)
        except msi.Error as e:
            log.write(ctx, "Could not set acl (admin:null) for collection: " + coll)
            return '1'

    # All went well
    return '0'


def determine_vault_target(ctx, folder):
    """Determine vault target path for a folder."""

    group = collection_group_name(ctx, folder)
    if group == '':
        log.write(ctx, "Cannot determine which research group " + + " ibelongs to")
        return ""

    parts = group.split('-')
    base_name = '-'.join(parts[1:])

    parts = folder.split('/')
    datapackage_name = parts[-1]

    if len(datapackage_name) > 235:
        datapackage_name = datapackage_name[0:235]

    ret = msi.get_icat_time(ctx, '', 'unix')
    timestamp = ret['arguments'][0].lstrip('0')

    vault_group_name = constants.IIVAULTPREFIX + base_name

    # Create target and ensure it does not exist already
    i = 0
    target_base = "/" + user.zone(ctx) + "/home/" + vault_group_name + "/" + datapackage_name + "[" + timestamp + "]"
    target = target_base
    while collection.exists(ctx, target):
        i += 1
        target = target_base + "[" + str(i) + "]"

    return target


def collection_group_name(callback, coll):
    """Return the name of the group a collection belongs to."""
    # Retrieve all access user IDs on collection.
    iter = genquery.row_iterator(
        "COLL_ACCESS_USER_ID",
        "COLL_NAME = '{}'".format(coll),
        genquery.AS_LIST, callback
    )

    for row in iter:
        id = row[0]

        # Retrieve all group names with this ID.
        iter2 = genquery.row_iterator(
            "USER_GROUP_NAME",
            "USER_GROUP_ID = '{}'".format(id),
            genquery.AS_LIST, callback
        )

        for row2 in iter2:
            group_name = row2[0]

            # Check if group is a research or intake group.
            if group_name.startswith("research-") or group_name.startswith("intake-"):
                return group_name

    for row in iter:
        id = row[0]
        for row2 in iter2:
            group_name = row2[0]

            # Check if group is a datamanager or vault group.
            if group_name.startswith("datamanager-") or group_name.startswith("vault-"):
                return group_name

    # No results found. Not a group folder
    log.write(callback, "{} does not belong to a research or intake group or is not available to current user.".format(coll))
    return ""


rule_collection_group_name = rule.make(inputs=[0], outputs=[1])(collection_group_name)


def get_org_metadata(ctx, path, object_type=pathutil.ObjectType.COLL):
    """Obtain a (k,v) list of all organisation metadata on a given collection or data object."""
    typ = 'DATA' if object_type is pathutil.ObjectType.DATA else 'COLL'

    return [(k, v) for k, v
            in Query(ctx, 'META_{}_ATTR_NAME, META_{}_ATTR_VALUE'.format(typ, typ),
                     "META_{}_ATTR_NAME like '{}%'".format(typ, constants.UUORGMETADATAPREFIX)
                     + (" AND COLL_NAME = '{}' AND DATA_NAME = '{}'".format(*pathutil.chop(path))
                        if object_type is pathutil.ObjectType.DATA
                        else " AND COLL_NAME = '{}'".format(path)))]


def get_locks(ctx, path, org_metadata=None, object_type=pathutil.ObjectType.COLL):
    """Return all locks on a collection or data object (includes locks on parents and children)."""
    if org_metadata is None:
        org_metadata = get_org_metadata(ctx, path, object_type=object_type)

    return [root for k, root in org_metadata
            if k == constants.IILOCKATTRNAME
            and (root.startswith(path) or path.startswith(root))]


@api.make()
def api_folder_get_locks(ctx, coll):
    """Return a list of locks on a collection."""
    return get_locks(ctx, coll)


def has_locks(ctx, coll, org_metadata=None):
    """Check whether a lock exists on the given collection, its parents or children."""
    return len(get_locks(ctx, coll, org_metadata=org_metadata)) > 0


def is_locked(ctx, coll, org_metadata=None):
    """Check whether a lock exists on the given collection itself or a parent collection.

    Locks on subcollections are not counted.
    """
    locks = get_locks(ctx, coll, org_metadata=org_metadata)

    # Count only locks that exist on the coll itself or its parents.
    return len([x for x in locks if coll.startswith(x)]) > 0


def is_data_locked(ctx, path, org_metadata=None):
    """Check whether a lock exists on the given data object."""
    locks = get_locks(ctx, path, org_metadata=org_metadata, object_type=pathutil.ObjectType.DATA)

    return len(locks) > 0


def get_status(ctx, path, org_metadata=None):
    """Get the status of a research folder."""
    if org_metadata is None:
        org_metadata = get_org_metadata(ctx, path)

    # Don't care about duplicate attr names here.
    org_metadata = dict(org_metadata)
    if constants.IISTATUSATTRNAME in org_metadata:
        x = org_metadata[constants.IISTATUSATTRNAME]
        try:
            return constants.research_package_state(x)
        except Exception as e:
            log.write(ctx, 'Invalid folder status <{}>'.format(x))

    return constants.research_package_state.FOLDER


def datamanager_exists(ctx, coll):
    """Check if a datamanager exists for a given collection."""
    group_name = collection_group_name(ctx, coll)
    category = group.get_category(ctx, group_name)

    return group.exists(ctx, "datamanager-" + category)
