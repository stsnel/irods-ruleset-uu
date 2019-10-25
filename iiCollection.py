# \file      iiCollection.py
# \brief     Functions to retrieve unformation about collections.
# \author    Lazlo Westerhof
# \copyright Copyright (c) 2019, Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE.


@define_as_rule('iiCollectionGroupName',
                inputs=[0], outputs=[1],
                handler=RuleOutput.STORE)
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
    callback.writeLine("serverLog", "{} does not belong to a research or intake group or is not available to current user.".format(coll))
    return ""