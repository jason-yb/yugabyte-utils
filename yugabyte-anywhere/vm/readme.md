# VM related scripts for Yugabyte Anywhere

## fix-replace-node.sql
This script will correct the universe metadata in the Yugabyte Anywhere database in the event of a failed operation where one node is being replaced and another VM is being added.  You should not run this operation without prior support engagement to confirm it is safe and correct to execute this action.

To run this, copy the sql file over to the Yugabyte Anywhere VM, then connect to postgres on the Yugabyte Anywhere and run as follows:
```
psql -h 127.0.0.1 -p 5432 -U postgres -d yugaware -f fix-replace-node.sql
```
This will create a backup of the universe table called universe_replace_node_backup_date_time (where date_time is YYYYMMDD_HH24MISS when run) and the update all universes found correcting those in an error state.

<small>*psql is in /opt/yugabyte/software/{version}/pgsql/bin*</small>