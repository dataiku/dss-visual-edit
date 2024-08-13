Feature: Visual Edit can lookup labels in a separate dataset.
    Background:
        Given the webapp "bodh8Xz" has the configuration from "./features/linked_dataset.label.feature.json"

    @cleanup_projects
    Scenario Outline: Linked record key is a string.
        Given a managed dataset "products" on connection "<connection>"
            | string  | string  | string   |
            | id      | company | location |
            | Answers |         | fr       |
            | DSS     |         | gaule    |
        And a managed dataset "companies" on connection "<connection>"
            | string      | string   | string    |
            | id          | name     | continent |
            | dataikuid   | Dataiku  | Europe    |
            | othertechid | CoolTech | Mars      |
        And I start the webapp
        And I navigate to the webapp
        Then the label for key "dataikuid" in dataset "companies" is "Dataiku"

        Examples:
            | connection         |
            | local_dku_pg       |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Linked record key is an integer.
        Given a managed dataset "products" on connection "<connection>"
            | string  | int     | string   |
            | id      | company | location |
            | Answers | 10      | fr       |
            | DSS     | 10      | gaule    |
        And a managed dataset "companies" on connection "<connection>"
            | int | string   | string    |
            | id  | name     | continent |
            | 0   | Dataiku  | Europe    |
            | 1   | CoolTech | Mars      |
        And I start the webapp
        And I navigate to the webapp
        Then the label for key "0" in dataset "companies" is "Dataiku"

        Examples:
            | connection         |
            | local_dku_pg       |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Linked record key is a float.
        Given a managed dataset "products" on connection "<connection>"
            | string  | float   | string   |
            | id      | company | location |
            | Answers | 10.1    | fr       |
            | DSS     | 10.2    | gaule    |
        And a managed dataset "companies" on connection "<connection>"
            | float | string   | string    |
            | id    | name     | continent |
            | 0.1   | Dataiku  | Europe    |
            | 0.2   | CoolTech | Mars      |
        And I start the webapp
        And I navigate to the webapp
        Then the label for key "0.2" in dataset "companies" is "CoolTech"

        Examples:
            | connection         |
            | local_dku_pg       |
            | filesystem_managed |