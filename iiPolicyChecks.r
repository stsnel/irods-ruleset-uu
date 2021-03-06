# \file      iiPolicyChecks.r
# \brief     Helper function to check for policy pre and post conditions
#            used by the locking mechanism and the folder status transition mechanism.
# \author    Paul Frederiks
# \author    Lazlo Westerhof
# \copyright Copyright (c) 2016-2018, Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE.

# \brief Check validity of requested folder status transition in a research area.
#
# \param[in] fromstatus    folder status before requested transition
# \param[in] tostatus      folder status after requested transition
#
iiIsStatusTransitionLegal(*fromstatus, *tostatus) {
	*legal = false;
	# IIFOLDERTRANSTIONS should be defined in iiConstants.r and lists all the legal status transitions
	foreach(*legaltransition in IIFOLDERTRANSITIONS) {
		(*legalfrom, *legalto) = *legaltransition;
		if (*legalfrom == *fromstatus && *legalto == *tostatus) {
			*legal = true;
			break;
		}
	}
	*legal;
}

# \brief Check validity of requested status transition in the vault.
#
# \param[in] fromstatus    folder status before requested transition
# \param[in] tostatus      folder status after requested transition
#
iiIsVaultStatusTransitionLegal(*fromstatus, *tostatus) {
	*legal = false;
	foreach(*legaltransition in IIVAULTTRANSITIONS) {
		(*legalfrom, *legalto) = *legaltransition;
		if (*legalfrom == *fromstatus && *legalto == *tostatus) {
			*legal = true;
			break;
		}
	}
	*legal;
}

# \brief Return a list of locks on an object.
#
# \param[in] objPath  path of collection or data object
# \param[out] locks   list of locks with the rootCollection of each lock as value
#
iiGetLocks(*objPath, *locks) {
	*locks = list();
	*lockattrname = IILOCKATTRNAME;
	msiGetObjType(*objPath, *objType);
	if (*objType == '-d') {
		uuChopPath(*objPath, *collection, *dataName);
		foreach (*row in SELECT META_DATA_ATTR_VALUE
					WHERE COLL_NAME = *collection
					  AND DATA_NAME = *dataName
					  AND META_DATA_ATTR_NAME = *lockattrname
			) {
				*rootCollection= *row.META_DATA_ATTR_VALUE;
				*locks = cons(*rootCollection, *locks);
			}
	} else {
		foreach (*row in SELECT META_COLL_ATTR_VALUE
					WHERE COLL_NAME = *objPath
					  AND META_COLL_ATTR_NAME = *lockattrname
			) {
				*rootCollection = *row.META_COLL_ATTR_VALUE;
				*locks = cons(*rootCollection, *locks);
		}
	}
}


# \brief Check if user metadata can be modified.
#
# \param[in] option          parameter of the action passed to the PEP. 'add', 'set' or 'rm'
# \param[in] itemType        type of item (-C for collection, -d for data object)
# \param[in] itemName        name of item (path in case of collection or data object)
# \param[in] attributeName   attribute name of AVU
# \param[out] allowed        boolean to indicate if the action is allowed
# \param[out] reason         reason the action is not allowed\
#
iiCanModifyUserMetadata(*option, *itemType, *itemName, *attributeName, *allowed, *reason) {
	*allowed = false;
	*reason = "Unknown error";

	iiGetLocks(*itemName, *locks);
	if (size(*locks) > 0) {
		if (*itemType == "-C") {
			foreach(*rootCollection in *locks) {
				if (strlen(*rootCollection) > strlen(*itemName)) {
					*allowed = true;
					*reason = "Lock found, but in subcollection *rootCollection";
				} else {
					*allowed = false;
					*reason = "Lock found, starting from *rootCollection";
					break;
				}
			}
		} else {
			*reason = "Locks found. *locks";
		}
	} else {
		*allowed = true;
		*reason = "No locks found";
	}

	#DEBUG writeLine("serverLog", "iiCanModifyUserMetadata: *itemName; allowed=*allowed; reason=*reason");
}


# \brief Check if a research folder status transition is legal.
#
# \param[in] folder
# \param[in] transitionFrom  current status to transition from
# \param[in] transitionTo    new status to transition to
# \param[out] allowed        boolean to indicate if the action is allowed
# \param[out] reason         reason the action is not allowed
#
iiCanTransitionFolderStatus(*folder, *transitionFrom, *transitionTo, *actor, *allowed, *reason) {
	*allowed = false;
	*reason = "Unknown error";
	if (iiIsStatusTransitionLegal(*transitionFrom, *transitionTo)) {
		*allowed = true;
		*reason = "Legal status transition. *transitionFrom -> *transitionTo";
	} else {
		if (*transitionFrom == FOLDER) {
			*reason = "Illegal status transition. Current folder has no status.";
		} else {
			*reason = "Illegal status transition. Current status is *transitionFrom.";
		}
		succeed;
	}

	if (*transitionTo == SUBMITTED) {
			*metadataJsonPath = *folder ++ "/" ++ IIJSONMETADATA;
			if (!uuFileExists(*metadataJsonPath)) {
					*allowed = false;
					*reason = "Metadata missing, unable to submit this folder.";
					succeed;
			} else {
					*status     = "";
					*statusInfo = "";
					rule_meta_validate(*metadataJsonPath, *status, *statusInfo);
					if (*status != "0") {
							*allowed = false;
							*reason = "Metadata is invalid, please check metadata form.";
							succeed;
					}
			}
	}

	if (*transitionTo == ACCEPTED || *transitionTo == REJECTED) {
		*groupName = "";
		*err1 = errorcode(rule_collection_group_name(*folder, *groupName));
		*err2 = errorcode(uuGroupGetCategory(*groupName, *category, *subcategory));
		*err3 = errorcode(uuGroupExists("datamanager-*category", *datamanagerExists));
		if (*err1 < 0 || *err2 < 0 || *err3 < 0) {
			*allowed = false;
			*reason = "Could not determine if datamanager-*category exists";
			succeed;
		}
		if (*datamanagerExists) {
			uuGroupGetMemberType("datamanager-*category", *actor, *userTypeIfDatamanager);
			if (*userTypeIfDatamanager == "normal" || *userTypeIfDatamanager == "manager") {
				*allowed = true;
				*reason = "Folder is *transitionTo by *actor from datamanager-*category";
			} else {
				*allowed = false;
				*reason = "Only a member of datamanager-*category is allowed to accept or reject a submitted folder";
				succeed;
			}
		} else {
			*allowed = true;
			*reason = "When no datamanager group exists, submitted folders are automatically accepted";
		}
	}

	if (*transitionTo == SECURED) {
		*allowed = false;
		*reason = "Only a rodsadmin is allowed to secure a folder to the vault";
		succeed;
	}

	if (*allowed) {
		iiGetLocks(*folder, *locks);
		if (size(*locks) > 0) {
			foreach(*rootCollection in *locks) {
				if (*rootCollection != *folder) {
					*allowed = false;
					*reason = "Found lock(s) starting from *rootCollection";
					break;
				}
			}
		}
	}
}


# \brief Check if a vault folder status transition is legal.
#
# \param[in] folder
# \param[in] transitionFrom  current status
# \param[in] transitionTo    status to transition to
# \param[in] actor           user name of actor requesting the transition
# \param[out] allowed        boolean to indicate if the action is allowed
# \param[out] reason         reason the action is not allowed
#
iiCanTransitionVaultStatus(*folder, *transitionFrom, *transitionTo, *actor, *allowed, *reason) {
	*allowed = false;
	*reason = "Unknown error";
	if (iiIsVaultStatusTransitionLegal(*transitionFrom, *transitionTo)) {
		*allowed = true;
		*reason = "Legal status transition. *transitionFrom -> *transitionTo";
	} else {
		*reason = "Illegal status transition. Current status is *transitionFrom.";
		succeed;
	}

	if (*transitionTo == PUBLISHED) {
		iiGetDOIFromMetadata(*folder, *yodaDOI);
		if (*yodaDOI == "") {
			*allowed = false;
			*reason = "*folder has no DOI"
			succeed;
		}

		iiGetLandingPageFromMetadata(*folder, *landingPage);
		if (*landingPage == "") {
			*allowed = false;
			*reason = "*folder has no landing page";
			succeed;
		}
	}
}
