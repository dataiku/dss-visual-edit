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
            | string    | string  | string    |
            | id        | name    | continent |
            | dataikuid | Dataiku | Europe    |
            | datadogid | Datadog | Mars      |
        And I start the webapp
        And I navigate to the webapp
        Then the lookup result for term "Data" in dataset "companies"
            | label   | value     | continent |
            | Datadog | datadogid | Mars      |
            | Dataiku | dataikuid | Europe    |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Linked record key is an integer.
        Given a managed dataset "products" on connection "<connection>"
            | string  | int     | string   |
            | id      | company | location |
            | Answers | 10      | fr       |
            | DSS     | 11      | gaule    |
        And a managed dataset "companies" on connection "<connection>"
            | int | string  | string    |
            | id  | name    | continent |
            | 10  | Dataiku | Europe    |
            | 11  | Datadog | Mars      |
        And I start the webapp
        And I navigate to the webapp
        Then the lookup result for term "Data" in dataset "companies"
            | label   | value | continent |
            | Datadog | 11    | Mars      |
            | Dataiku | 10    | Europe    |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Linked record key is a float.
        Given a managed dataset "products" on connection "<connection>"
            | string  | float   | string   |
            | id      | company | location |
            | Answers | 10.1    | fr       |
            | DSS     | 10.2    | gaule    |
        And a managed dataset "companies" on connection "<connection>"
            | float | string  | string    |
            | id    | name    | continent |
            | 11.1  | Dataiku | Europe    |
            | 11.2  | Datadog | Mars      |
        And I start the webapp
        And I navigate to the webapp
        Then the lookup result for term "Datadog" in dataset "companies"
            | label   | value | continent |
            | Datadog | 11.2  | Mars      |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |