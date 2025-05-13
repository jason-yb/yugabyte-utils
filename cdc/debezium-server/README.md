## Running in Docker

1. Start the Yugabyte database, create the database, tables, 

   ```sh
   docker compose up -d yugabyte
   ```
2. Start the Debezium server:

   ```sh
   docker compose up -d debezium-server
   ```

3. Insert more rows into the table:

   ```sh
   docker exec -it yugabyte bash -c "/home/yugabyte/bin/ysqlsh --echo-queries --host \$(hostname) --dbname=demo -c \"INSERT INTO public.products (created_at, category, ean, price, quantity, rating, title, vendor)  VALUES
   ('2025-05-03 12:00:00', 'Electronics', '1234567890123', 199.99, 5000, 4.5, 'Smartphone A', 'Vendor1'),
   ('2025-05-03 12:15:00', 'Home Appliances', '2345678901234', 299.99, 4000, 4.7, 'Vacuum Cleaner B', 'Vendor2'),
   ('2025-05-03 12:30:00', 'Furniture', '3456789012345', 149.99, 3500, 4.2, 'Sofa C', 'Vendor3'),
   ('2025-05-03 12:45:00', 'Toys', '4567890123456', 29.99, 6000, 4.8, 'Lego Set D', 'Vendor4'),
   ('2025-05-03 13:00:00', 'Clothing', '5678901234567', 49.99, 7000, 4.0, 'Jacket E', 'Vendor6')\" "

   docker exec -it yugabyte bash -c "/home/yugabyte/bin/ysqlsh --echo-queries --host \$(hostname) --dbname=demo -c \"INSERT INTO attributes (props) SELECT hstore(ARRAY['color',(ARRAY['red','blue','green','yellow','black'])[floor(random() * 5 + 1)],'size',(ARRAY['S','M','L','XL'])[floor(random() * 4 + 1)]]) FROM generate_series(1, 500)\" "
   ```

4. Check the Pub/Sub subscription 

   ```sh
   gcloud pubsub subscriptions pull --project emea-poc --limit 5 projects/emea-poc/subscriptions/just-pull [--auto-ack]
   ```

## Useful Commands

Create an interactive Yugabyte CLI shell in the Yugabyte container:

```sh
docker exec -it yugabyte bash -c '/home/yugabyte/bin/ysqlsh --echo-queries --host $(hostname)'
```

