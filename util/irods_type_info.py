# -*- coding: utf-8 -*-
"""Allows converting certain irods types to string representation for debugging purposes

Importing this module (anywhere) adds stringifyability to some frequently-used
irods_types types.
"""

import irods_types


def pyify(x):
    # Turn irods type into equivalent python type, if possible.
    return x._pyify() if '_pyify' in dir(x) else str(x)


irods_types.c_string._pyify   = lambda self: str(self)
irods_types.c_string.__repr__ = lambda self: repr(pyify(self))

irods_types.char_array._pyify   = lambda self: str(self)
irods_types.char_array.__repr__ = lambda self: repr(pyify(self))

irods_types.int_array._pyify   = lambda self: list(self)
irods_types.int_array.__repr__ = lambda self: repr(pyify(self))

irods_types.c_string_array._pyify   = lambda self: map(pyify, list(self))
irods_types.c_string_array.__repr__ = lambda self: repr(pyify(self))

irods_types.InxIvalPair._pyify   = lambda self: dict(zip(pyify(self.inx), pyify(self.value)))
irods_types.InxIvalPair.__repr__ = lambda self: repr(pyify(self))

irods_types.KeyValPair._pyify   = lambda self: (pyify(self.key), pyify(self.value))
irods_types.KeyValPair.__repr__ = lambda self: repr(pyify(self))

irods_types.InxValPair._pyify   = lambda self: zip(pyify(self.inx), pyify(self.value))
irods_types.InxValPair.__repr__ = lambda self: repr(pyify(self))

irods_types.GenQueryInp.__repr__ = \
    lambda self: 'GenQuery(select {} where {})'.format(
        ', '.join(map(col_name, pyify(self.selectInp))),
        ' and '.join(map(lambda kv: '{} {}'.format(col_name(kv[0]), kv[1]),
                     pyify(self.sqlCondInp))))

# (add more as needed)

col_name = lambda i: filter(lambda kv: kv[1] == i, cols)[0][0]

cols =\
    [('ZONE_ID', 101),
     ('ZONE_NAME', 102),
     ('ZONE_TYPE', 103),
     ('ZONE_CONNECTION', 104),
     ('ZONE_COMMENT', 105),
     ('ZONE_CREATE_TIME', 106),
     ('ZONE_MODIFY_TIME', 107),
     ('USER_ID', 201),
     ('USER_NAME', 202),
     ('USER_TYPE', 203),
     ('USER_ZONE', 204),
     ('USER_INFO', 206),
     ('USER_COMMENT', 207),
     ('USER_CREATE_TIME', 208),
     ('USER_MODIFY_TIME', 209),
     ('USER_DN_INVALID', 205),
     ('R_RESC_ID', 301),
     ('R_RESC_NAME', 302),
     ('R_ZONE_NAME', 303),
     ('R_TYPE_NAME', 304),
     ('R_CLASS_NAME', 305),
     ('R_LOC', 306),
     ('R_VAULT_PATH', 307),
     ('R_FREE_SPACE', 308),
     ('R_RESC_INFO', 309),
     ('R_RESC_COMMENT', 310),
     ('R_CREATE_TIME', 311),
     ('R_MODIFY_TIME', 312),
     ('R_RESC_STATUS', 313),
     ('R_FREE_SPACE_TIME', 314),
     ('R_RESC_CHILDREN', 315),
     ('R_RESC_CONTEXT', 316),
     ('R_RESC_PARENT', 317),
     ('R_RESC_PARENT_CONTEXT', 318),
     ('D_DATA_ID', 401),
     ('D_COLL_ID', 402),
     ('DATA_NAME', 403),
     ('DATA_REPL_NUM', 404),
     ('DATA_VERSION', 405),
     ('DATA_TYPE_NAME', 406),
     ('DATA_SIZE', 407),
     ('D_RESC_NAME', 409),
     ('D_DATA_PATH', 410),
     ('D_OWNER_NAME', 411),
     ('D_OWNER_ZONE', 412),
     ('D_REPL_STATUS', 413),
     ('D_DATA_STATUS', 414),
     ('D_DATA_CHECKSUM', 415),
     ('D_EXPIRY', 416),
     ('D_MAP_ID', 417),
     ('D_COMMENTS', 418),
     ('D_CREATE_TIME', 419),
     ('D_MODIFY_TIME', 420),
     ('DATA_MODE', 421),
     ('D_RESC_HIER', 422),
     ('D_RESC_ID', 423),
     ('COLL_ID', 500),
     ('COLL_NAME', 501),
     ('COLL_PARENT_NAME', 502),
     ('COLL_OWNER_NAME', 503),
     ('COLL_OWNER_ZONE', 504),
     ('COLL_MAP_ID', 505),
     ('COLL_INHERITANCE', 506),
     ('COLL_COMMENTS', 507),
     ('COLL_CREATE_TIME', 508),
     ('COLL_MODIFY_TIME', 509),
     ('COLL_TYPE', 510),
     ('COLL_INFO1', 511),
     ('COLL_INFO2', 512),
     ('META_DATA_ATTR_NAME', 600),
     ('META_DATA_ATTR_VALUE', 601),
     ('META_DATA_ATTR_UNITS', 602),
     ('META_DATA_ATTR_ID', 603),
     ('META_DATA_CREATE_TIME', 604),
     ('META_DATA_MODIFY_TIME', 605),
     ('META_COLL_ATTR_NAME', 610),
     ('META_COLL_ATTR_VALUE', 611),
     ('META_COLL_ATTR_UNITS', 612),
     ('META_COLL_ATTR_ID', 613),
     ('META_COLL_CREATE_TIME', 614),
     ('META_COLL_MODIFY_TIME', 615),
     ('META_NAMESPACE_COLL', 620),
     ('META_NAMESPACE_DATA', 621),
     ('META_NAMESPACE_RESC', 622),
     ('META_NAMESPACE_USER', 623),
     ('META_NAMESPACE_RESC_GROUP', 624),
     ('META_NAMESPACE_RULE', 625),
     ('META_NAMESPACE_MSRVC', 626),
     ('META_NAMESPACE_MET2', 627),
     ('META_RESC_ATTR_NAME', 630),
     ('META_RESC_ATTR_VALUE', 631),
     ('META_RESC_ATTR_UNITS', 632),
     ('META_RESC_ATTR_ID', 633),
     ('META_RESC_CREATE_TIME', 634),
     ('META_RESC_MODIFY_TIME', 635),
     ('META_USER_ATTR_NAME', 640),
     ('META_USER_ATTR_VALUE', 641),
     ('META_USER_ATTR_UNITS', 642),
     ('META_USER_ATTR_ID', 643),
     ('META_USER_CREATE_TIME', 644),
     ('META_USER_MODIFY_TIME', 645),
     ('META_RESC_GROUP_ATTR_NAME', 650),
     ('META_RESC_GROUP_ATTR_VALUE', 651),
     ('META_RESC_GROUP_ATTR_UNITS', 652),
     ('META_RESC_GROUP_ATTR_ID', 653),
     ('META_RESC_GROUP_CREATE_TIME', 654),
     ('META_RESC_GROUP_MODIFY_TIME', 655),
     ('META_RULE_ATTR_NAME', 660),
     ('META_RULE_ATTR_VALUE', 661),
     ('META_RULE_ATTR_UNITS', 662),
     ('META_RULE_ATTR_ID', 663),
     ('META_RULE_CREATE_TIME', 664),
     ('META_RULE_MODIFY_TIME', 665),
     ('META_MSRVC_ATTR_NAME', 670),
     ('META_MSRVC_ATTR_VALUE', 671),
     ('META_MSRVC_ATTR_UNITS', 672),
     ('META_MSRVC_ATTR_ID', 673),
     ('META_MSRVC_CREATE_TIME', 674),
     ('META_MSRVC_MODIFY_TIME', 675),
     ('META_MET2_ATTR_NAME', 680),
     ('META_MET2_ATTR_VALUE', 681),
     ('META_MET2_ATTR_UNITS', 682),
     ('META_MET2_ATTR_ID', 683),
     ('META_MET2_CREATE_TIME', 684),
     ('META_MET2_MODIFY_TIME', 685),
     ('DATA_ACCESS_TYPE', 700),
     ('DATA_ACCESS_NAME', 701),
     ('DATA_TOKEN_NAMESPACE', 702),
     ('DATA_ACCESS_USER_ID', 703),
     ('DATA_ACCESS_DATA_ID', 704),
     ('COLL_ACCESS_TYPE', 710),
     ('COLL_ACCESS_NAME', 711),
     ('COLL_TOKEN_NAMESPACE', 712),
     ('COLL_ACCESS_USER_ID', 713),
     ('COLL_ACCESS_COLL_ID', 714),
     ('RESC_ACCESS_TYPE', 720),
     ('RESC_ACCESS_NAME', 721),
     ('RESC_TOKEN_NAMESPACE', 722),
     ('RESC_ACCESS_USER_ID', 723),
     ('RESC_ACCESS_RESC_ID', 724),
     ('META_ACCESS_TYPE', 730),
     ('META_ACCESS_NAME', 731),
     ('META_TOKEN_NAMESPACE', 732),
     ('META_ACCESS_USER_ID', 733),
     ('META_ACCESS_META_ID', 734),
     ('RULE_ACCESS_TYPE', 740),
     ('RULE_ACCESS_NAME', 741),
     ('RULE_TOKEN_NAMESPACE', 742),
     ('RULE_ACCESS_USER_ID', 743),
     ('RULE_ACCESS_RULE_ID', 744),
     ('MSRVC_ACCESS_TYPE', 750),
     ('MSRVC_ACCESS_NAME', 751),
     ('MSRVC_TOKEN_NAMESPACE', 752),
     ('MSRVC_ACCESS_USER_ID', 753),
     ('MSRVC_ACCESS_MSRVC_ID', 754),
     ('USER_GROUP_ID', 900),
     ('USER_GROUP_NAME', 901),
     ('RULE_EXEC_ID', 1000),
     ('RULE_EXEC_NAME', 1001),
     ('RULE_EXEC_REI_FILE_PATH', 1002),
     ('RULE_EXEC_USER_NAME', 1003),
     ('RULE_EXEC_ADDRESS', 1004),
     ('RULE_EXEC_TIME', 1005),
     ('RULE_EXEC_FREQUENCY', 1006),
     ('RULE_EXEC_PRIORITY', 1007),
     ('RULE_EXEC_ESTIMATED_EXE_TIME', 1008),
     ('RULE_EXEC_NOTIFICATION_ADDR', 1009),
     ('RULE_EXEC_LAST_EXE_TIME', 1010),
     ('RULE_EXEC_STATUS', 1011),
     ('TOKEN_NAMESPACE', 1100),
     ('TOKEN_ID', 1101),
     ('TOKEN_NAME', 1102),
     ('TOKEN_VALUE', 1103),
     ('TOKEN_VALUE2', 1104),
     ('TOKEN_VALUE3', 1105),
     ('TOKEN_COMMENT', 1106),
     ('AUDIT_OBJ_ID', 1200),
     ('AUDIT_USER_ID', 1201),
     ('AUDIT_ACTION_ID', 1202),
     ('AUDIT_COMMENT', 1203),
     ('AUDIT_CREATE_TIME', 1204),
     ('AUDIT_MODIFY_TIME', 1205),
     ('AUDIT_RANGE_START', 1200),
     ('AUDIT_RANGE_END', 1299),
     ('COLL_USER_NAME', 1300),
     ('COLL_USER_ZONE', 1301),
     ('DATA_USER_NAME', 1310),
     ('DATA_USER_ZONE', 1311),
     ('RESC_USER_NAME', 1320),
     ('RESC_USER_ZONE', 1321),
     ('SL_HOST_NAME', 1400),
     ('SL_RESC_NAME', 1401),
     ('SL_CPU_USED', 1402),
     ('SL_MEM_USED', 1403),
     ('SL_SWAP_USED', 1404),
     ('SL_RUNQ_LOAD', 1405),
     ('SL_DISK_SPACE', 1406),
     ('SL_NET_INPUT', 1407),
     ('SL_NET_OUTPUT', 1408),
     ('SL_NET_OUTPUT', 1408),
     ('SL_CREATE_TIME', 1409),
     ('SLD_RESC_NAME', 1500),
     ('SLD_LOAD_FACTOR', 1501),
     ('SLD_CREATE_TIME', 1502),
     ('USER_AUTH_ID', 1600),
     ('USER_DN', 1601),
     ('RULE_ID', 1700),
     ('RULE_VERSION', 1701),
     ('RULE_BASE_NAME', 1702),
     ('RULE_NAME', 1703),
     ('RULE_EVENT', 1704),
     ('RULE_CONDITION', 1705),
     ('RULE_BODY', 1706),
     ('RULE_RECOVERY', 1707),
     ('RULE_STATUS', 1708),
     ('RULE_OWNER_NAME', 1709),
     ('RULE_OWNER_ZONE', 1710),
     ('RULE_DESCR_1', 1711),
     ('RULE_DESCR_2', 1712),
     ('RULE_INPUT_PARAMS', 1713),
     ('RULE_OUTPUT_PARAMS', 1714),
     ('RULE_DOLLAR_VARS', 1715),
     ('RULE_ICAT_ELEMENTS', 1716),
     ('RULE_SIDEEFFECTS', 1717),
     ('RULE_COMMENT', 1718),
     ('RULE_CREATE_TIME', 1719),
     ('RULE_MODIFY_TIME', 1720),
     ('RULE_BASE_MAP_VERSION', 1721),
     ('RULE_BASE_MAP_BASE_NAME', 1722),
     ('RULE_BASE_MAP_OWNER_NAME', 1723),
     ('RULE_BASE_MAP_OWNER_ZONE', 1724),
     ('RULE_BASE_MAP_COMMENT', 1725),
     ('RULE_BASE_MAP_CREATE_TIME', 1726),
     ('RULE_BASE_MAP_MODIFY_TIME', 1727),
     ('RULE_BASE_MAP_PRIORITY', 1728),
     ('DVM_ID', 1800),
     ('DVM_VERSION', 1801),
     ('DVM_BASE_NAME', 1802),
     ('DVM_EXT_VAR_NAME', 1803),
     ('DVM_CONDITION', 1804),
     ('DVM_INT_MAP_PATH', 1805),
     ('DVM_STATUS', 1806),
     ('DVM_OWNER_NAME', 1807),
     ('DVM_OWNER_ZONE', 1808),
     ('DVM_COMMENT', 1809),
     ('DVM_CREATE_TIME', 1810),
     ('DVM_MODIFY_TIME', 1811),
     ('DVM_BASE_MAP_VERSION', 1812),
     ('DVM_BASE_MAP_BASE_NAME', 1813),
     ('DVM_BASE_MAP_OWNER_NAME', 1814),
     ('DVM_BASE_MAP_OWNER_ZONE', 1815),
     ('DVM_BASE_MAP_COMMENT', 1816),
     ('DVM_BASE_MAP_CREATE_TIME', 1817),
     ('DVM_BASE_MAP_MODIFY_TIME', 1818),
     ('FNM_ID', 1900),
     ('FNM_VERSION', 1901),
     ('FNM_BASE_NAME', 1902),
     ('FNM_EXT_FUNC_NAME', 1903),
     ('FNM_INT_FUNC_NAME', 1904),
     ('FNM_STATUS', 1905),
     ('FNM_OWNER_NAME', 1906),
     ('FNM_OWNER_ZONE', 1907),
     ('FNM_COMMENT', 1908),
     ('FNM_CREATE_TIME', 1909),
     ('FNM_MODIFY_TIME', 1910),
     ('FNM_BASE_MAP_VERSION', 1911),
     ('FNM_BASE_MAP_BASE_NAME', 1912),
     ('FNM_BASE_MAP_OWNER_NAME', 1913),
     ('FNM_BASE_MAP_OWNER_ZONE', 1914),
     ('FNM_BASE_MAP_COMMENT', 1915),
     ('FNM_BASE_MAP_CREATE_TIME', 1916),
     ('FNM_BASE_MAP_MODIFY_TIME', 1917),
     ('QUOTA_USER_ID', 2000),
     ('QUOTA_RESC_ID', 2001),
     ('QUOTA_LIMIT', 2002),
     ('QUOTA_OVER', 2003),
     ('QUOTA_MODIFY_TIME', 2004),
     ('QUOTA_USAGE_USER_ID', 2010),
     ('QUOTA_USAGE_RESC_ID', 2011),
     ('QUOTA_USAGE', 2012),
     ('QUOTA_USAGE_MODIFY_TIME', 2013),
     ('QUOTA_RESC_NAME', 2020),
     ('QUOTA_USER_NAME', 2021),
     ('QUOTA_USER_ZONE', 2022),
     ('QUOTA_USER_TYPE', 2023),
     ('MSRVC_ID', 2100),
     ('MSRVC_NAME', 2101),
     ('MSRVC_SIGNATURE', 2102),
     ('MSRVC_DOXYGEN', 2103),
     ('MSRVC_VARIATIONS', 2104),
     ('MSRVC_STATUS', 2105),
     ('MSRVC_OWNER_NAME', 2106),
     ('MSRVC_OWNER_ZONE', 2107),
     ('MSRVC_COMMENT', 2108),
     ('MSRVC_CREATE_TIME', 2109),
     ('MSRVC_MODIFY_TIME', 2110),
     ('MSRVC_VERSION', 2111),
     ('MSRVC_HOST', 2112),
     ('MSRVC_LOCATION', 2113),
     ('MSRVC_LANGUAGE', 2114),
     ('MSRVC_TYPE_NAME', 2115),
     ('MSRVC_MODULE_NAME', 2116),
     ('MSRVC_VER_OWNER_NAME', 2150),
     ('MSRVC_VER_OWNER_ZONE', 2151),
     ('MSRVC_VER_COMMENT', 2152),
     ('MSRVC_VER_CREATE_TIME', 2153),
     ('MSRVC_VER_MODIFY_TIME', 2154),
     ('TICKET_ID', 2200),
     ('TICKET_STRING', 2201),
     ('TICKET_TYPE', 2202),
     ('TICKET_USER_ID', 2203),
     ('TICKET_OBJECT_ID', 2204),
     ('TICKET_OBJECT_TYPE', 2205),
     ('TICKET_USES_LIMIT', 2206),
     ('TICKET_USES_COUNT', 2207),
     ('TICKET_EXPIRY_TS', 2208),
     ('TICKET_CREATE_TIME', 2209),
     ('TICKET_MODIFY_TIME', 2210),
     ('TICKET_WRITE_FILE_COUNT', 2211),
     ('TICKET_WRITE_FILE_LIMIT', 2212),
     ('TICKET_WRITE_BYTE_COUNT', 2213),
     ('TICKET_WRITE_BYTE_LIMIT', 2214),
     ('TICKET_ALLOWED_HOST_TICKET_ID', 2220),
     ('TICKET_ALLOWED_HOST', 2221),
     ('TICKET_ALLOWED_USER_TICKET_ID', 2222),
     ('TICKET_ALLOWED_USER_NAME', 2223),
     ('TICKET_ALLOWED_GROUP_TICKET_ID', 2224),
     ('TICKET_ALLOWED_GROUP_NAME', 2225),
     ('TICKET_DATA_NAME', 2226),
     ('TICKET_DATA_COLL_NAME', 2227),
     ('TICKET_COLL_NAME', 2228),
     ('TICKET_OWNER_NAME', 2229),
     ('TICKET_OWNER_ZONE', 2230)]
