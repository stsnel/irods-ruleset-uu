# \file      iiSchemaLocations.py
# \brief     Functions for handling schemaLocations within any yoda-metadata.xml.
# \author    Lazlo Westerhof
# \author    Felix Croes
# \author    Harm de Raaff
# \copyright Copyright (c) 2018-2019 Utrecht University. All rights reserved.
# \license   GPLv3, see LICENSE.

import os
from collections import namedtuple
from enum import Enum
import hashlib
import base64
import irods_types
import xml.etree.ElementTree as ET
import time


# Based upon the category of the current yoda-metadata.xml file, return the XSD schema involved.
# Schema location depends on the category the yoda-metadata.xml belongs to.
# If the specific category XSD does not exist, fall back to /default/research.xsd or /default/vault.xsd.
def getSchemaLocation(callback, rods_zone, group_name):
    category = '-1'
    schemaCategory = 'default'

    if 'research-' in group_name:
        area = 'research'
    elif 'vault-' in group_name:
        area = 'vault'
    else:
        return '-1'

    # Find out category based on current group_name.
    ret_val = callback.msiMakeGenQuery(
        "META_USER_ATTR_NAME, META_USER_ATTR_VALUE",
        "USER_GROUP_NAME = '" + group_name + "' AND  META_USER_ATTR_NAME like 'category'",
        irods_types.GenQueryInp())
    query = ret_val["arguments"][2]

    ret_val = callback.msiExecGenQuery(query, irods_types.GenQueryOut())
    result = ret_val["arguments"][1]

    if result.rowCnt != 0:
        # Check each data object in batch.
        for row in range(0, result.rowCnt):
            attrValue = result.sqlResult[1].row(row)
            category = attrValue

    if category != '-1':
        # Test whether found category actually has a collection with XSD's.
        # If not, fall back to default schema collection. Otherwise use category schema collection
        # /tempZone/yoda/schemas/default
        # - metadata.xsd
        # - vault.xsd
        xsdCollectionName = '/' + rods_zone + '/yoda/schemas/' + category
        ret_val = callback.msiMakeGenQuery(
            "COLL_NAME",
            "DATA_NAME like '%%.xsd' AND COLL_NAME = '" + xsdCollectionName + "'",
            irods_types.GenQueryInp())
        query = ret_val["arguments"][2]

        ret_val = callback.msiExecGenQuery(query, irods_types.GenQueryOut())
        result = ret_val["arguments"][1]

        if result.rowCnt != 0:
            schemaCategory = category    # As collection is present, the schemaCategory can be assigned the category

    return 'https://schemas.yoda.uu.nl/' + schemaCategory + ' ' + area + '.xsd'


# \brief getLatestVaultMetadataXml
#
# \param[in] vaultPackage
#
# \return metadataXmlPath
def getLatestVaultMetadataXml(callback, vaultPackage):
    dataNameQuery = "yoda-metadata[%].xml"
    ret_val = callback.msiMakeGenQuery(
        "DATA_NAME, DATA_SIZE",
        "COLL_NAME = '" + vaultPackage + "' AND DATA_NAME like '" + dataNameQuery + "'",
        irods_types.GenQueryInp())
    query = ret_val["arguments"][2]

    ret_val = callback.msiExecGenQuery(query, irods_types.GenQueryOut())

    # Loop through all XMLs.
    dataName = ""
    while True:
        result = ret_val["arguments"][1]
        for row in range(result.rowCnt):
            data_name = result.sqlResult[0].row(row)
            data_size = int(result.sqlResult[1].row(row))

            if dataName == "" or (dataName < data_name and len(dataName) <= len(data_name)):
                dataName = data_name

        # Continue with this query.
        if result.continueInx == 0:
            break

        ret_val = callback.msiGetMoreRows(query, result, 0)
    callback.msiCloseGenQuery(query, result)

    return dataName


# \brief getDataObjSize
#
# \param[in] coll_name Data object collection name
# \param[in] data_name Data object name
#
# \return Data object size
def getDataObjSize(callback, coll_name, data_name):
    ret_val = callback.msiMakeGenQuery(
        "DATA_SIZE",
        "COLL_NAME = '%s' AND DATA_NAME = '%s'" % (coll_name, data_name),
        irods_types.GenQueryInp())
    query = ret_val["arguments"][2]

    ret_val = callback.msiExecGenQuery(query, irods_types.GenQueryOut())
    result = ret_val["arguments"][1]

    data_size = 0
    if result.rowCnt != 0:
        for row in range(0, result.rowCnt):
            data_size = result.sqlResult[0].row(row)

    return data_size


# \brief getUserNameFromUserId
#
# \param[in] user_id User id
#
# \return User name
def getUserNameFromUserId(callback, user_id):
    ret_val = callback.msiMakeGenQuery(
        "USER_NAME",
        "USER_ID = '%s'" % (str(user_id)),
        irods_types.GenQueryInp())
    query = ret_val["arguments"][2]

    ret_val = callback.msiExecGenQuery(query, irods_types.GenQueryOut())
    result = ret_val["arguments"][1]

    user_name = ''
    if result.rowCnt != 0:
        for row in range(0, result.rowCnt):
            user_name = result.sqlResult[0].row(row)

    return user_name


# \brief When inheritance is missing we need to copy ACL's when introducing new data in vault package.
#
# \param[in] path               Path of object that needs the permissions of parent
# \param[in] recursive_flag     either "default" for no recursion or "recursive"
#
def copyACLsFromParent(callback, path, recursive_flag):
    parent = os.path.dirname(path)

    ret_val = callback.msiMakeGenQuery(
        "COLL_ACCESS_NAME, COLL_ACCESS_USER_ID",
        "COLL_NAME = '" + parent + "'",
        irods_types.GenQueryInp())
    query = ret_val["arguments"][2]

    ret_val = callback.msiExecGenQuery(query, irods_types.GenQueryOut())
    result = ret_val["arguments"][1]

    if result.rowCnt != 0:
        for row in range(0, result.rowCnt):
            access_name = result.sqlResult[0].row(row)
            user_id = int(result.sqlResult[1].row(row))
            user_name = getUserNameFromUserId(callback, user_id)

            if access_name == "own":
                callback.writeString("serverLog", "iiCopyACLsFromParent: granting own to <" + user_name + "> on <" + path + "> with recursiveFlag <" + recursive_flag + ">")
                callback.msiSetACL(recursive_flag, "own", user_name, path)
            elif access_name == "read object":
                callback.writeString("serverLog", "iiCopyACLsFromParent: granting own to <" + user_name + "> on <" + path + "> with recursiveFlag <" + recursive_flag + ">")
                callback.msiSetACL(recursive_flag, "read", user_name, path)
            elif access_name == "modify object":
                callback.writeString("serverLog", "iiCopyACLsFromParent: granting own to <" + user_name + "> on <" + path + "> with recursiveFlag <" + recursive_flag + ">")
                callback.msiSetACL(recursive_flag, "write", user_name, path)


# Actual check for presence of schemaLocation within the passed yoda-metadata.xml.
# If schemaLocation is not present it is added.
# Schema location is dependent on category the yoda-metadata.xml belongs to.
# If the specific XSD does not exist, fall back to /default/research.xsd or /default/vault.xsd.
def addSchemaLocationToMetadataXml(callback, rods_zone, coll_name, group_name, data_size, data_name):
    ret_val = callback.msiDataObjOpen('objPath=' + coll_name + "/" + data_name, 0)
    fileHandle = ret_val['arguments'][1]
    ret_val = callback.msiDataObjRead(fileHandle, data_size, irods_types.BytesBuf())
    callback.msiDataObjClose(fileHandle, 0)
    read_buf = ret_val['arguments'][2]
    xmlText = ''.join(read_buf.buf)

    # Parse XML
    root = ET.fromstring(xmlText)

    # Check if schemaLocation attribute is present.
    # If not, add schemaLocation attribute.
    if not root.attrib:
        # Retrieve Schema location to be added.
        schemaLocation = getSchemaLocation(callback, rods_zone, group_name)
        if schemaLocation != '-1':
            root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            root.set('xsi:schemaLocation', schemaLocation)
            newXmlString = ET.tostring(root, encoding='UTF-8')

            if "research" in group_name:
                ofFlags = 'forceFlag='  # File already exists, so must be overwritten.
                xml_file = coll_name + "/" + data_name
                ret_val = callback.msiDataObjCreate(xml_file, ofFlags, 0)
            elif "vault" in group_name:
                ofFlags = ''
                xml_file = coll_name + '/yoda-metadata[' + str(int(time.time())) + '].xml'
                ret_val = callback.msiDataObjCreate(xml_file, ofFlags, 0)
                copyACLsFromParent(callback, xml_file, "default")

            fileHandle = ret_val['arguments'][2]
            callback.msiDataObjWrite(fileHandle, newXmlString, 0)
            callback.msiDataObjClose(fileHandle, 0)
            callback.writeString("serverLog", "[UPDATE METADATA SCHEMA] %s" % (xml_file))


# Loop through all collections with yoda-metadata.xml data objects.
def checkMetadataForSchemaLocationBatch(callback, rods_zone, coll_id, batch, pause):
    import time

    # Find all research and vault collections, ordered by COLL_ID.
    ret_val = callback.msiMakeGenQuery(
        "ORDER(COLL_ID), COLL_NAME",
        "COLL_NAME like '/%s/home/%%' AND DATA_NAME like 'yoda-metadata%%xml' AND COLL_ID >= '%d'" % (rods_zone, coll_id),
        irods_types.GenQueryInp())
    query = ret_val["arguments"][2]

    ret_val = callback.msiExecGenQuery(query, irods_types.GenQueryOut())
    result = ret_val["arguments"][1]

    if result.rowCnt != 0:
        # Check each collection in batch.
        for row in range(min(batch, result.rowCnt)):
            coll_id = int(result.sqlResult[0].row(row))
            coll_name = result.sqlResult[1].row(row)

            # Determine Vault or Research handling
            pathParts = coll_name.split('/')

            try:
                group_name = pathParts[3]
                if 'research-' in group_name:
                    data_size = getDataObjSize(callback, coll_name, "yoda-metadata.xml")
                    addSchemaLocationToMetadataXml(callback, rods_zone, coll_name, group_name, data_size, "yoda-metadata.xml")
                elif 'vault-' in group_name:
                    # Parent collections should not be 'original'. Those files must remain untouched.
                    if pathParts[-1] != 'original':
                        data_name = getLatestVaultMetadataXml(callback, coll_name)
                        data_size = getDataObjSize(callback, coll_name, data_name)
                        addSchemaLocationToMetadataXml(callback, rods_zone, coll_name, group_name, data_size, data_name)
            except:
                pass

            # Sleep briefly between checks.
            time.sleep(pause)

        # The next collection to check must have a higher COLL_ID.
        coll_id = coll_id + 1
    else:
        # All done.
        coll_id = 0

    return coll_id


# \brief Check metadata XML for schema location.
# \param[in] coll_id  first COLL_ID to check
# \param[in] batch    batch size, <= 256
# \param[in] pause    pause between checks (float)
# \param[in] delay    delay between batches in seconds
#
def iiCheckMetadataForSchemaLocation(rule_args, callback, rei):
    import session_vars

    coll_id = int(rule_args[0])
    batch = int(rule_args[1])
    pause = float(rule_args[2])
    delay = int(rule_args[3])
    rods_zone = session_vars.get_map(rei)["client_user"]["irods_zone"]

    # Check one batch of vault data.
    coll_id = checkMetadataForSchemaLocationBatch(callback, rods_zone, coll_id, batch, pause)

    if coll_id != 0:
        # Check the next batch after a delay.
        callback.delayExec(
            "<PLUSET>%ds</PLUSET>" % delay,
            "iiCheckMetadataForSchemaLocation('%d', '%d', '%f', '%d')" % (coll_id, batch, pause, delay),
            "")
