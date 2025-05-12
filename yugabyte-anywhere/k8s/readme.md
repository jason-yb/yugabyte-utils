# k8s related scripts for Yugabyte Anywhere

## fix-replace-node.sql
This script will correct the universe metadata in the Yugabyte Anywhere database after a replace node has been run on a k8s universe.
The menu option for replace node will be disabled for k8s in subsequent releases to prevent this being used as it is not required/supported for k8s.

To run this, copy the sql file over to the yugabtye pod:
```
kubectl cp /your/path/fix-replace-node.sql /yba-yugaware-0:/tmp/fix-replace-node.sql
```
Then connect to the postgres container on the Yugabyte Anywhere pod and run as follows:
```
psql -U postgres -d yugaware -f /tmp/fix-replace-node.sql
```
This will create a backup of the universe table called universe_replace_node_backup_date_time (where date_time is YYYYMMDD_HH24MISS when run) and the update all universes found correcting those in an error state.
