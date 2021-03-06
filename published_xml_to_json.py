# -*- coding: utf-8 -*-
"""Functions for transform Yoda metadata XML to JSON."""

__copyright__ = 'Copyright (c) 2019, Utrecht University'
__license__   = 'GPLv3, see LICENSE'

import os

from util import *

__all__ = ['rule_published_xml_to_json_check_published_metadata_xml_for_transformation_to_json']


def transformPublishedMetadataXmlToJson(ctx, rods_zone, publish_collection, xml_data_name, data_name_json):
    """Convert current yoda-metadata.xml to yoda-metadata.json.

    :param ctx:                iRODS context
    :param rods_zone:          Zone name
    :param publish_collection: Collection name of metadata XML
    :param xml_data_name:      Data name of metadata XML that requires transformation
    :param data_name_json:     Name of data object to be created containing the
    """
    # This function simply transforms given data_name to a Json data object.
    # No further intelligence required further.
    # Perhaps handling within vault??

    ofFlags = ''
    json_file = publish_collection + '/' + data_name_json

    ret_val = ctx.msiDataObjCreate(json_file, ofFlags, 0)

    # copyACLsFromParent(ctx, json_file, "default")

    xmlDataDict = getMetadataXmlAsDict(ctx, publish_collection + "/" + xml_data_name)

    # take category including version from declared namespace in xml
    category_version = xmlDataDict['metadata']['@xmlns'].split('/')[-1]

    dictSchema = getActiveJsonSchemaAsDict(ctx, rods_zone, category_version)

    newJsonDataString = transformYodaXmlDataToJson(ctx, dictSchema, xmlDataDict)

    fileHandle = ret_val['arguments'][2]
    ctx.msiDataObjWrite(fileHandle, newJsonDataString, 0)
    ctx.msiDataObjClose(fileHandle, 0)

    log.write(ctx, "[ADDED METADATA.JSON AFTER TRANSFORMATION] %s" % (json_file))


def iiCheckPublishedMetadataXmlForTransformationToJsonBatch(ctx, rods_zone, data_id, batch, pause, publicHost, yodaInstance, yodaPrefix):
    """Loop through all metadata xml data objects within '/tempZone/yoda/publication'.

    If NO corresponding json is found in that collection,
    the corresponding yoda-metadata.xml must be converted to json as an extra file - yoda-metadata.json.
    The resulting file must be copied to moai collection as well.

    :param ctx:           iRODS context
    :param rods_zone:     Zone name
    :param data_id:       Data id to start searching from
    :param batch:         Batch size, <= 256
    :param pause:         Pause between checks (float)
    :param publicHost:    Hostname of public host
    :param yodaInstance:  Name of Yoda instance
    :param yodaPrefix:    Prefix of Yoda DOIs from this instance

    :returns: integer -- Data_id to continue with in next batch.
                         If data_id =0, no more data objects were found. Batch is finished.
    """
    publication_collection = '/' + rods_zone + '/yoda/publication'
    iter = genquery.row_iterator(
        "ORDER(DATA_ID), DATA_NAME, COLL_ID",
        "COLL_NAME = '%s' AND DATA_NAME like '%%.xml' AND DATA_ID >= '%d'" % (publication_collection, data_id),
        genquery.AS_LIST, ctx
    )

    # Check each collection in batch.
    for row in iter:
        data_id = int(row[0])
        data_name_xml = row[1]
        coll_id = int(row[2])
        pathParts = coll_name.split('/')
        data_name_no_extension = os.path.splitext(data_name)[0]  # the base name of the data object without extension
        data_name_json = data_name_no_extension + '.json'

        try:
            # First make sure that no metadata json file exists already in the published collection .
            # If so, no transformation is required and the json file needs not be copied into the MOAI area.
            iter2 = genquery.row_iterator(
                "ORDER(COLL_ID), COLL_NAME",
                "DATA_NAME = '%s' AND COLL_ID = '%d'" % (data_name_json, coll_id),
                genquery.AS_LIST, ctx)

            if not next(iter2, False):
                # At this moment only default schema is used. So not required to figure out which schema is necessary
                transformPublishedMetadataXmlToJson(ctx, rods_zone, publication_collection, data_name_xml, data_name_json)
                ctx.iiCopyTransformedPublicationToMOAI(data_name_json, publication_collection, publicHost, yodaInstance, yodaPrefix)
        except Exception:
            pass

        # Sleep briefly between checks.
        time.sleep(pause)

        # The next data_id to check must have a higher DATA_ID
        data_id = data_id + 1
    else:
        # All done.
        data_id = 0

    return data_id


def rule_published_xml_to_json_check_published_metadata_xml_for_transformation_to_json(rule_args, ctx, rei):
    """Convert published metadata XML that residedes in 'published' collection to JSON - batchwise.

    :param rule_args: [0] First COLL_ID to check - initial = 0
                      [1] Batch size, <= 256
                      [2] Pause between checks (float)
                      [3] Delay between batches in seconds
                      [4] Hostname of public host
                      [5]  Name of Yoda instance
                      [6] Prefix of Yoda DOIs from this instance
    :param ctx:       iRODS context
    :param rei:       The rei struct
    """
    data_id = int(rule_args[0])
    batch = int(rule_args[1])
    pause = float(rule_args[2])
    delay = int(rule_args[3])
    publicHost = rule_args[4]
    yodaInstance = rule_args[5]
    yodaPrefix = rule_args[6]
    rods_zone = session_vars.get_map(rei)["client_user"]["irods_zone"]

    # Check one	batch of metadata schemas.
    # If no more data_ids are found in the main/single publication folder, the function returns 0
    data_id = iiCheckPublishedMetadataXmlForTransformationToJsonBatch(ctx, rods_zone, data_id, batch, pause, publicHost, yodaInstance, yodaPrefix)

    if coll_id != 0:
        # Check the next batch after a delay.
        ctx.delayExec(
            "<PLUSET>%ds</PLUSET>" % delay,
            "rule_published_xml_to_json_check_published_metadata_xml_for_transformation_to_json('%d', '%d', '%f', '%d', '%s', '%s', '%s')" % (data_id, batch, pause, delay, publicHost, yodaInstance, yodaPrefix),
            "")
