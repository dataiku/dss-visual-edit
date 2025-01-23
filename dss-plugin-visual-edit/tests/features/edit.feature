Feature: Visual Edit generic edition.
    Background:
        Given the webapp "bodh8Xz" has the configuration from "./features/edit.feature.json"

    @cleanup_projects
    Scenario Outline: Two columns can be edited at once.
        Given a managed dataset "products" on connection "<connection>"
            | string  | string    | string   |
            | id      | company   | location |
            | Answers | BS plugin | fr       |
            | DSS     | dku       | gaule    |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | Answers             | company       | dataiku      |
            | id           | Answers             | location      | france       |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key,column_name"
            | key     | user   | column_name | value   | action |
            | Answers | reader | company     | dataiku | update |
            | Answers | reader | location    | france  | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | location       | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id      | company | location | last_action | first_action |
            | Answers | dataiku | france   | update      | update       |
        And the dataset "products_edited" has the following schema
            | name     | type   |
            | id       | string |
            | company  | string |
            | location | string |
        And the dataset "products_edited" contains the following using compound key "id"
            | id      | company | location |
            | Answers | dataiku | france   |
            | DSS     | dku     | gaule    |

        Examples:
            | connection         |
            | filesystem_managed |

    # @cleanup_projects
    # Scenario Outline: The latest edit overrides previous edits made on the same cell.
    #     Given a managed dataset "products" on connection "<connection>"
    #         | string  | string    | string   |
    #         | id      | company   | location |
    #         | Answers | BS plugin | fr       |
    #         | DSS     | dku       | gaule    |
    #     And I start the webapp
    #     And I navigate to the webapp
    #     When I edit rows as such
    #         | primary_keys | primary_keys_values | edited_column | edited_value |
    #         | id           | Answers             | company       | dku          |
    #     And I edit rows as such
    #         | primary_keys | primary_keys_values | edited_column | edited_value |
    #         | id           | Answers             | company       | dataiku      |
    #     And I do a forced recursive build of dataset "products_edited"
    #     Then the dataset "products_editlog" contains the following using compound key "key,value"
    #         | key     | user   | column_name | value   | action |
    #         | Answers | reader | company     | dku     | update |
    #         | Answers | reader | company     | dataiku | update |
    #     And the dataset "products_edits" has the following schema
    #         | name           | type   |
    #         | id             | string |
    #         | company        | string |
    #         | location       | string |
    #         | last_edit_date | string |
    #         | last_action    | string |
    #         | first_action   | string |
    #     And the dataset "products_edits" contains the following using compound key "id"
    #         | id      | company | location | last_action | first_action |
    #         | Answers | dataiku |          | update      | update       |
    #     And the dataset "products_edited" has the following schema
    #         | name     | type   |
    #         | id       | string |
    #         | company  | string |
    #         | location | string |
    #     And the dataset "products_edited" contains the following using compound key "id"
    #         | id      | company | location |
    #         | Answers | dataiku | fr       |
    #         | DSS     | dku     | gaule    |

    #     Examples:
    #         | connection         |
    #         | filesystem_managed |

    # @cleanup_projects
    # Scenario Outline: A dataset with more than 1000 rows (with SQL dataset, code paths is different) can be edited.
    #     Given a managed dataset "products" on connection "<connection>"
    #         | int | string  | string   |
    #         | id  | company | location |
    #     And the CSV file "./assets/csv_with_more_than_1000_rows.csv" is written in dataset "products"
    #     And I start the webapp
    #     And I navigate to the webapp
    #     When I edit rows as such
    #         | primary_keys | primary_keys_values | edited_column | edited_value    |
    #         | id           | 0                   | company       | integrationtest |
    #     And I do a forced recursive build of dataset "products_edited"
    #     Then the dataset "products_editlog" contains the following using compound key "key,value"
    #         | key | user   | column_name | value           | action |
    #         | 0   | reader | company     | integrationtest | update |
    #     And the dataset "products_edits" has the following schema
    #         | name           | type   |
    #         | id             | string |
    #         | company        | string |
    #         | location       | string |
    #         | last_edit_date | string |
    #         | last_action    | string |
    #         | first_action   | string |
    #     And the dataset "products_edits" contains the following using compound key "id"
    #         | id | company         | location | last_action | first_action |
    #         | 0  | integrationtest |          | update      | update       |
    #     And the dataset "products_edited" has the following schema
    #         | name     | type   |
    #         | id       | bigint |
    #         | company  | string |
    #         | location | string |

    #     Examples:
    #         | connection         |
    #         | filesystem_managed |