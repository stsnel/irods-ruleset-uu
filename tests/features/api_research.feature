Feature: Research API

    Scenario: Research folder add
        Given user "researcher" is authenticated
        And the Yoda research folder add API is queried with "<folder>" and "<collection>"
        Then the response status code is "200"
        And folder "<folder>" exists in "<collection>"

        Examples:
            | folder           | collection                      |
            | api_test_folder1 | /tempZone/home/research-initial |
            | api_test_folder2 | /tempZone/home/research-initial |

    Scenario: Research folder rename
        Given user "researcher" is authenticated
        And the Yoda research folder rename API is queried with "<folder_old>", "<folder>" and "<collection>"
        Then the response status code is "200"
        And folder "<folder>" exists in "<collection>"

        Examples:
            | folder_old       | folder                   | collection                      |
            | api_test_folder1 | api_test_folder1_renamed | /tempZone/home/research-initial |

    Scenario: Research folder delete
        Given user "researcher" is authenticated
        And the Yoda research folder delete API is queried with "<folder>" and "<collection>"
        Then the response status code is "200"
        And folder "<folder>" does not exists in "<collection>"

        Examples:
            | folder                   | collection                      |
            | api_test_folder1_renamed | /tempZone/home/research-initial |
            | api_test_folder2         | /tempZone/home/research-initial |

    Scenario: Research file copy
        Given user "researcher" is authenticated
        And the Yoda research file copy API is queried with "<file>", "<copy>" and "<collection>"
        Then the response status code is "200"
        And file "<file>" exists in "<collection>"
        And file "<copy>" exists in "<collection>"

        Examples:
            | file               | copy                    | collection                       |
            | yoda-metadata.json | yoda-metadata_copy.json | /tempZone/home/research-initial1 |

    Scenario: Research file rename
        Given user "researcher" is authenticated
        And the Yoda research file rename API is queried with "<file>", "<file_renamed>" and "<collection>"
        Then the response status code is "200"
        And file "<file>" does not exist in "<collection>"
        And file "<file_renamed>" exists in "<collection>"

        Examples:
            | file                    | file_renamed               | collection                       |
            | yoda-metadata_copy.json | yoda-metadata_renamed.json | /tempZone/home/research-initial1 |

    Scenario: Research file upload
        Given user "researcher" is authenticated
        And a file "<file>" is uploaded in "<folder>"
        Then the response status code is "200"
        And file "<file>" exists in "<collection>"

        Examples:
            | file                 | folder             | collection                       |
            | upload_test_file.txt | /research-initial1 | /tempZone/home/research-initial1 |

    Scenario: Research file delete
        Given user "researcher" is authenticated
        And the Yoda research file delete API is queried with "<file>" and "<collection>"
        Then the response status code is "200"
        And file "<file>" does not exist in "<collection>"

        Examples:
            | file                       | collection                       |
            | yoda-metadata_renamed.json | /tempZone/home/research-initial1 |
            | upload_test_file.txt       | /tempZone/home/research-initial1 |

    Scenario: Research collection details
        Given user "researcher" is authenticated
        And the Yoda research system metadata API is queried with "<collection>"
        Then the response status code is "200"

        Examples:
            | collection                      |
            | /tempZone/home/research-initial |

    Scenario: Research collection details
        Given user "researcher" is authenticated
        And the Yoda research collection details API is queried with "<collection>"
        Then the response status code is "200"

        Examples:
            | collection                      |
            | /tempZone/home/research-initial |
