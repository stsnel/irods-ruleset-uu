# \file      iiFolderStatusTransitions.r
# \brief     Status transitions for folders in the research space.
# \author    Paul Frederiks
# \author    Lazlo Westerhof
# \copyright Copyright (c) 2015-2019 Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE.

# \brief iiFolderStatus
#
# \param[in]  folder	    Path of folder
# \param[out] folderStatus  Current status of folder
#
iiFolderStatus(*folder, *folderStatus) {
	*folderStatusKey = IISTATUSATTRNAME;
	*folderStatus = FOLDER;
	foreach(*row in SELECT META_COLL_ATTR_VALUE WHERE COLL_NAME = *folder AND META_COLL_ATTR_NAME = *folderStatusKey) {
		*folderStatus = *row.META_COLL_ATTR_VALUE;
	}
}

# \brief Schedule copy-to-vault (asynchronously).
#
iiScheduleCopyToVault() {
	delay ("<PLUSET>1s</PLUSET>") {
		msiExecCmd("scheduled-copytovault.sh", "", "", "", 0, *out);
	}
}


# \brief iiFolderDatamanagerAction
#
# \param[in] folder
# \param[out] newFolderStatus Status to set as datamanager. Either ACCEPTED or REJECTED
# \param[out] status          status of the action
# \param[out] statusInfo      Informative message when action was not successfull
#
iiFolderDatamanagerAction(*folder, *newFolderStatus, *status, *statusInfo) {
	*status = "Unknown";
	*statusInfo = "An internal error has occurred";

	# Check if folder is a research group.
	*groupName = "";
	*err = errorcode(rule_collection_group_name(*folder, *groupName));
	if (*err < 0) {
		*status = "NoResearchGroup";
		*statusInfo = "*folder is not accessible possibly due to insufficient rights or as it is not part of a research group. Therefore, the requested action can not be performed";
		succeed;
	} else {
		# Research group, determine datamanager group.
		uuGroupGetCategory(*groupName, *category, *subcategory);
               *datamanagerGroup = "datamanager-*category";
	}

	*actor = uuClientFullName;
	*aclKv.actor = *actor;
	*err = errorcode(msiSudoObjAclSet("recursive", "write", *datamanagerGroup, *folder, *aclKv));
	if (*err < 0) {
		*status = "PermissionDenied";
		iiCanDatamanagerAclSet(*folder, *actor, *datamanagerGroup, 0, "write", *allowed, *reason);
		if (*allowed) {
			*statusInfo = "Could not acquire datamanager access to *folder.";
		} else {
			*statusInfo = *reason;
		}
		succeed;
	}
	if (*newFolderStatus == REJECTED) {
		# get permission to unlock ancestors, too
		uuChopPath(*folder, *parent, *child);
		while(*parent != "/$rodsZoneClient/home") {
			msiSudoObjAclSet("", "write", *datamanagerGroup, *parent, *aclKv);
			uuChopPath(*parent, *coll, *child);
			*parent = *coll;
		}
	}
	*folderStatusStr = IISTATUSATTRNAME ++ "=" ++ *newFolderStatus;
	msiString2KeyValPair(*folderStatusStr, *folderStatusKvp);
	*err = errormsg(msiSetKeyValuePairsToObj(*folderStatusKvp, *folder, "-C"), *msg);
	if (*err < 0) {
		iiFolderStatus(*folder, *currentFolderStatus);
		iiCanTransitionFolderStatus(*folder, *currentFolderStatus, *newFolderStatus, *actor, *allowed, *reason);
		if (!*allowed) {
			*status = "PermissionDenied";
			*statusInfo = *reason;
		} else {
			if (*err == -818000) {
				*status = "PermissionDenied";
				*statusInfo = "User is not permitted to modify folder status";
			} else {
				*status = "Unrecoverable";
				*statusInfo = "*err - *msg";
			}
		}
	}
	*err = errormsg(msiSudoObjAclSet("recursive", "read", *datamanagerGroup, *folder, *aclKv), *msg);
	if (*err < 0) {
		*status = "FailedToRemoveTemporaryAccess";
		iiCanDatamanagerAclSet(*folder, *actor, *datamanagerGroup, 0, "read", *allowed, *reason);
		if (*allowed) {
			*statusInfo = "*err - *msg";
		} else {
			*statusInfo = *reason;
		}
		succeed;
	}
	if (*newFolderStatus == REJECTED) {
		# remove permission to modify ancestors
		uuChopPath(*folder, *parent, *child);
		while(*parent != "/$rodsZoneClient/home") {
			msiSudoObjAclSet("", "read", *datamanagerGroup, *parent, *aclKv);
			uuChopPath(*parent, *coll, *child);
			*parent = *coll;
		}
	}
	if (*status == "Unknown") {
		*status = "Success";
		*statusInfo = "";
	}
}

# \brief iiFolderLockChange
#
# \param[in] rootCollection 	The COLL_NAME of the collection the dataset resides in
# \param[in] lockIt 		Boolean, true if the object should be locked.
#				if false, the lock is removed (if allowed)
# \param[out] status 		Zero if no errors, non-zero otherwise
#
iiFolderLockChange(*rootCollection, *lockIt, *status){
	msiString2KeyValPair("", *buffer);
	msiAddKeyVal(*buffer, IILOCKATTRNAME, *rootCollection)
	#DEBUG writeLine("ServerLog", "iiFolderLockChange: *buffer");
	if (*lockIt == "lock") {
		#DEBUG writeLine("serverLog", "iiFolderLockChange: recursive locking of *rootCollection");
		*direction = "forward";
		uuTreeWalk(*direction, *rootCollection, "iiAddMetadataToItem", *buffer, *error);
		if (*error == 0) {
			uuChopPath(*rootCollection, *parent, *child);
			while(*parent != "/$rodsZoneClient/home") {
				uuChopPath(*parent, *coll, *child);
				iiAddMetadataToItem(*coll, *child, true, *buffer, *error);
				*parent = *coll;
			}
		}
	} else {
		#DEBUG writeLine("serverLog", "iiFolderLockChange: recursive unlocking of *rootCollection");
		*direction="reverse";
		uuTreeWalk(*direction, *rootCollection, "iiRemoveMetadataFromItem", *buffer, *error);
		if (*error == 0) {
			uuChopPath(*rootCollection, *parent, *child);
			while(*parent != "/$rodsZoneClient/home") {
				uuChopPath(*parent, *coll, *child);
				iiRemoveMetadataFromItem(*coll, *child, true, *buffer, *error);
				*parent = *coll;
			}
		}

	}

	*status = "*error";
}

# \brief Return objectType string based on boolean itemIsCollection.
#
# \param[in] itemIsCollection	boolean usually returned by treewalk when item is a Collection
# \returnvalue		        iRODS objectType string. "-C" for Collection, "-d" for DataObject
#
iitypeabbreviation(*itemIsCollection) =  if *itemIsCollection then "-C" else "-d"

# \brief For use by uuTreewalk to add metadata.
#
# \param[in] itemParent            full iRODS path to the parent of this object
# \param[in] itemName              basename of collection or dataobject
# \param[in] itemIsCollection      true if the item is a collection
# \param[in,out] buffer            in/out Key-Value variable
# \param[out] error                errorcode in case of failure
#
iiAddMetadataToItem(*itemParent, *itemName, *itemIsCollection, *buffer, *error) {
	*objPath = "*itemParent/*itemName";
	*objType = iitypeabbreviation(*itemIsCollection);
	#DEBUG writeLine("serverLog", "iiAddMetadataToItem: Setting *buffer on *objPath");
	*error = errorcode(msiAssociateKeyValuePairsToObj(*buffer, *objPath, *objType));
}

# \brief For use by uuTreeWalk to remove metadata.
#
# \param[in] itemParent            full iRODS path to the parent of this object
# \param[in] itemName              basename of collection or dataobject
# \param[in] itemIsCollection      true if the item is a collection
# \param[in,out] buffer            in/out Key-Value variable
# \param[out] error                errorcode in case of failure
#
iiRemoveMetadataFromItem(*itemParent, *itemName, *itemIsCollection, *buffer, *error) {
	*objPath = "*itemParent/*itemName";
	*objType = iitypeabbreviation(*itemIsCollection);
	#DEBUG writeLine("serverLog", "iiRemoveMetadataKeyFromItem: Removing *buffer on *objPath");
	*error = errormsg(msiRemoveKeyValuePairsFromObj(*buffer, *objPath, *objType), *msg);
	if (*error < 0) {
		writeLine("serverLog", "iiRemoveMetadataFromItem: removing *buffer from *objPath failed with errorcode: *error");
		writeLine("serverLog", *msg);
		if (*error == -819000) {
			# This happens when metadata was already removed or never there.
			writeLine("serverLog", "iiRemoveMetadaFromItem: -819000 detected. Keep on trucking, this happens if metadata was already removed");
			*error = 0;
		}
	}
}
