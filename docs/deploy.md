# Deploying to production (automation node)

## Preliminary remarks

* When deploying a project with a data editing webapp, there would be two different editlog datasets: one on the Design node, one on the Automation node. This way, edits made on the Design node won't have any impact in production. These two editlog datasets would have the same name, but they should be on different data connections.
* While the datasets in a Dataiku project are typically on analytics database connections and managed by Dataiku, you may prefer to change the connection of the _editlog_ and _editlog\_pivoted_ datasets to an operational database, with constraints for the database used in Automation that would prevent accidental deletions and tampering with edits.
* We recommend using SQL connections for these datasets.

## Deployment steps

Initial deployment:

* Initialize the production editlog. Upon deploying the project bundle for the first time on the Automation node, the editlog dataset will exist and it will have a schema, but it may appear as having an invalid configuration. This would be the case when using a SQL connection, as the table used for the editlog in Automation won't be automatically created by the bundle deployment process. This is discussed in a dedicated section of this guide.
* Make sure that the version of the plugin installed on the Automation node is the same as on the Design node.

All deployments:

* Create a new bundle (do not include the contents of the editlog in the bundle, as it would replace edits made in production with those made on the design node).
* Build the dataset used by the webapp as the "original dataset" to edit.
* (Stop and) Start the webapp.

Demo videos:

* [Deploy to production](https://www.loom.com/share/e47c5d09871741c48062e3547108bb39)
* [Update in production](https://www.loom.com/share/8b806a65e50a4406b9ec3d4a31495205)

## Initializing the production editlog

### Simple procedure

A simple way to initialize the editlog is with a _reset edits_ scenario as described in the getting started guide. You can then delete the scenario, to make sure that it won't be used accidentally in the future (which would cause losing all edits).

### Secure procedure

>**For audit purposes, we strongly encourage to follow this procedure.**

In the context of audit, it is especially critical to make sure no tampering is possible. Three layers of security can be put in place for this:

- From a Dataiku permissions standpoint, limit access to the editlog dataset.
- Set up your editlog table so the `date` cannot be set freely (otherwise one may insert events "in the past"), and so that it is append-only.

We illustrate with SQL code for a Postgresql database.

* Use the `date` column as the primary key and make sure it's always set to the current date/time when data is inserted in this table (we're assuming that the date of the system running the database can't be tampered with).

```sql
CREATE TABLE editlog (
    date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP PRIMARY KEY,
    user VARCHAR(255),
    key VARCHAR(255)
);

CREATE OR REPLACE FUNCTION set_timestamp_id()
RETURNS TRIGGER AS $$
BEGIN
    NEW.date = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_timestamp_id_trigger
BEFORE INSERT ON editlog
FOR EACH ROW EXECUTE FUNCTION set_timestamp_id();
```

* Set this table to be append-only.

```sql
REVOKE ALL ON TABLE editlog FROM public;
GRANT SELECT, INSERT ON TABLE editlog TO your_user;
```

* Optional: raise an error if someone tries to update or delete data

```sql
CREATE OR REPLACE FUNCTION prevent_updates()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Table is append-only. Updates and deletes are not allowed.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_updates_trigger
BEFORE UPDATE OR DELETE ON editlog
FOR EACH ROW EXECUTE FUNCTION prevent_updates();
```

* Set up a Connection to this database, using the credentials of a database user with limited permissions (only SELECTs and INSERTs).

## Security considerations

### Protecting the editlog from interference

* The credentials used to write to the editlog have limited permissions. An audit trail from the database provider helps ensure that these permissions aren't altered.
* These credentials are not known by the Dataiku project designer, so they can't write to the database by sending requests directly to it.
* The only way for the project designer to tamper with the editlog is to make changes to the webapp code which leverages the Connection that writes to the database. Dataiku Govern guards around deploying projects that were tampered with (either at the Flow level, or at the Webapp and code level).

### Restricting access to the webapp

As any Dataiku webapp, it can either require authentication, or it can be made accessible to visitors who are not logged into Dataiku. We do not recommend the latter option, as anyone who has access to the webapp will be allowed to see the data that it exposes and to make edits. If, however, you do want to make the webapp accessible to unauthenticated visitors, their edits will be attributed to user "none" in the editlog.

When authentication is required:

* The webapp can only be used by users with a Reader license or above.
* It allows to read contents of the original dataset, of the associated editlog, and of the label and lookup columns of linked datasets (if any).
* Even though the name "Reader" might suggest that they can only read data, they webapp doesn't make a distinction between license types and Readers are able to make edits.
* You can restrict access to specified (groups of) users at the project level, via the Project > Security settings: only those with "Read Dashboard" permission will be able to use the webapp (i.e. see and edit data).
* You can restrict access at the webapp level, via the "Authorized users" property of the Visual Webapp settings. It is presented as a list; if it is not empty, only users whose identifiers are included in the list will be able to use the webapp (i.e. see and edit data).

Remember that the webapp only writes data to the editlog, not to the original dataset (which stays unchanged). The editlog pivoted and the edited datasets can only be changed by running the recipes that build them.

## Tips for production usage

When sharing the production webapp with business users, it's a good idea to tick "auto-start backend" in webapp settings, which will help make sure that the webapp is always available. In an effort to be conscious of your Dataiku instance's resources, we recommend running the webapp in containerized execution when available.

You can share a direct link to the webapp (or a dashboard that embeds it), but it can be easier for end-users to find it again in the future if it's added to a Workspace. Workspaces provide a friendlier way for business users to access all objects shared with them in Dataiku. If your end-users don't already use a Workspace, we recommend creating one for them and having them use Workspaces as their Dataiku home page.

If a domain-specific issue is detected downstream of edits, review the editlog to understand its root cause. If a cell was incorrectly edited, edit it again via the webapp, which will log the correct value; you can then build datasets downstream.
