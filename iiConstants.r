# \file
# \brief Constants for the ii rules. If architecture changes, only
# 			this file needs be adapted
#
# \author Jan de Mooij
# \copyright Copyright (c) 2016, Utrecht university. All rights reserved
# \license GPLv3, see LICENSE

# \brief uuIiGetGroupPrefix 	Get the prefix for a group collection
#
# \param[out] grpPrefix 		Group collection group prefix
uuIiGetGroupPrefix(*grpPrefix) {
	*grpPrefix = "grp-"
}

# \brief uuIigetIntakePrefix 	Get prefix for intake collection
# 
# \param[out] intakePrefix 		Prefix of intake collection, including
# 								the group prefix
uuIiGetIntakePrefix(*intakePrefix) {
	uuIiGetGroupPrefix(*grp);
	*intakePrefix = *grp
}

# \brief uuIiGetVaultPrefix 	Get prefix for vault collection
# 
# \param[out] vaultPrefix 		Prefix of vault collection, including
# 								the group prefix
uuIiGetVaultPrefix(*vaultPrefix) {
	uuIiGetGroupPrefix(*grp);
	*vaultPrefix = "vault-";
}

# \brief uuIiGetMetadataPrefix 	Get prefix for metadata which the portal uses
#								If this constant is updated, also update
# 								the PHP Portal config
# \param[out] metadataPrefix 	The prefix used for metadata by the portal
uuIiGetMetadataPrefix(*metadataPrefix) {
	*metadataPrefix = "ilab_";
}

# \brief uuIiIntakeLevel 		Get the depth at which level the intake
# 								takes place, i.e. which level is defined
# 								to be a dataset, which can have versions
#								and which can be snapshotted or archived
# 								MAKE SURE TO have this correspond to the
#								PHP Portal!
# 
# \param[out] *level 			The depth of the datapackage counted from
# 								anything below /<zone>/home/<level1>/<level2>...
uuIiIntakeLevel(*level) {
	*level = 2;
}

# \brief uuIiVersionPrefix 		Get the prefix used for versions (on top
# 								of the default metadata prefix)
# \param[out] versionPrefix 	The prefix used for versions in iRods metadata
uuIiVersionKey(*versionKey, *dependsKey) {
	uuIiGetMetadataPrefix(*prfx);
	*versionKey = *prfx ++ "version";
	*dependsKey = *prfx ++ "depends_on";
}

# \brief constants		Use constants for constants
# \author Paul Frederiks
# \constant IIMETADATAPREFIX	Prefix for metadata in ilab
IIMETADATAPREFIX = "ilab_"
# \constants IIGROUPPREFIX	Prefix for groups in ilab
IIGROUPPREFIX = "research-"

# \constant GENQMAXROWS Maximum number of rows returned by an iRODS GenQuery or msiGetMoreRows call
GENQMAXROWS = 256

# \constant DPTXTNAME	Name of text file that marks datapackages  
DPTXTNAME = ".yoda-datapackage.txt"

# \constant IIXSDDEFAULTNAME	Name of the fallback default xsd for ilab
IIXSDDEFAULTNAME = "default.xsd"

# \constant IIXSDCOLLECTION
IIXSDCOLLECTION = UUSYSTEMCOLLECTION ++ "/xsd"

# \constant IIXMLCOLLECTION
IIXMLCOLLECTION = UUSYSTEMCOLLECTION ++ "/xml"

# \constant IIXSLCOLLECTION
IIXSLCOLLECTION = UUSYSTEMCOLLECTION ++ "/xsl"

# \constant IIFORMELEMENTSCOLLECTION
IIFORMELEMENTSCOLLECTION = UUSYSTEMCOLLECTION ++ "/formelements"

# \constant IIFORMELEMENTSDEFAULTNAME
IIFORMELEMENTSDEFAULTNAME = "formelements.xml"

# \constant IIMETADATAXMLNAME
IIMETADATAXMLNAME = ".yoda-metadata.xml"

# \constant IIXSLDEFAULTNAME
IIXSLDEFAULTNAME = "metadata.xsl"
