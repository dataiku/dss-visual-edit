Feature: SQL, single primary key.
    Background:
        Given an existing webapp "UyLsbJ6" in project "VISUALEDITINTEGRATIONTESTS"
        And an emptied existing dataset named "locations_editlog"
        And an emptied existing dataset named "locations_edits"
        And an emptied existing dataset named "locations_edited"

    Scenario: Edit a string column.
        Given an existing dataset named "locations" with the following content
            | string  | string        | string   |
            | country | state         | capital  |
            | USA     | Texas         | New York |
            | France  | Ile de France | Paris    |
        When I edit rows as such
            | primary_keys  | primary_keys_values | edited_column | edited_value |
            | country;state | USA;Texas           | capital       | Austin       |
        And I do a forced recursive build of dataset "locations_edited"
        Then the dataset "locations_editlog" contains the following using compound key "key"
            | key              | column_name | value  | action |
            | ('USA', 'Texas') | capital     | Austin | update |
        And the dataset "locations_edited" contains the following using compound key "country"
            | country | state         | capital |
            | USA     | Texas         | Austin  |
            | France  | Ile de France | Paris   |

    Scenario: Edit an integer column.
        Given an existing dataset named "locations" with the following content
            | string  | string        | string  |
            | country | state         | capital |
            | USA     | Texas         | 0       |
            | France  | Ile de France | 10      |
        When I edit rows as such
            | primary_keys  | primary_keys_values | edited_column | edited_value |
            | country;state | USA;Texas           | capital       | 42           |
        And I do a forced recursive build of dataset "locations_edited"
        Then the dataset "locations_editlog" contains the following using compound key "key"
            | key              | column_name | value | action |
            | ('USA', 'Texas') | capital     | 42    | update |
        And the dataset "locations_edited" contains the following using compound key "country"
            | country | state         | capital |
            | USA     | Texas         | 42      |
            | France  | Ile de France | 10      |

    Scenario: Edit a float column.
        Given an existing dataset named "locations" with the following content
            | string  | string        | string  |
            | country | state         | capital |
            | USA     | Texas         | 0.1     |
            | France  | Ile de France | 11.2    |
        When I edit rows as such
            | primary_keys  | primary_keys_values | edited_column | edited_value |
            | country;state | USA;Texas           | capital       | 12.4         |
        And I do a forced recursive build of dataset "locations_edited"
        Then the dataset "locations_editlog" contains the following using compound key "key"
            | key              | column_name | value | action |
            | ('USA', 'Texas') | capital     | 12.4  | update |
        And the dataset "locations_edited" contains the following using compound key "country"
            | country | state         | capital |
            | USA     | Texas         | 12.4    |
            | France  | Ile de France | 11.2    |

    Scenario: Edit a boolean column.
        Given an existing dataset named "locations" with the following content
            | string  | string        | boolean |
            | country | state         | capital |
            | USA     | Texas         | false   |
            | France  | Ile de France | false   |
        When I edit rows as such
            | primary_keys  | primary_keys_values | edited_column | edited_value |
            | country;state | USA;Texas           | capital       | true         |
        And I do a forced recursive build of dataset "locations_edited"
        Then the dataset "locations_editlog" contains the following using compound key "key"
            | key              | column_name | value | action |
            | ('USA', 'Texas') | capital     | true  | update |
        And the dataset "locations_edited" contains the following using compound key "country"
            | country | state         | capital |
            | USA     | Texas         | true    |
            | France  | Ile de France | false   |