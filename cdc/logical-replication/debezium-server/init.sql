-- Create the demo database
CREATE DATABASE demo;

-- Connect to demo DB and set up schema + seed data
\c demo

-- Schema setup
\i share/schema.sql

-- Data insert
\i share/products.sql

-- Set the sequence to 300
SELECT setval('products_id_seq', 300, true);

-- Create table with hstore column
CREATE EXTENSION hstore;
CREATE TABLE attributes (
    id SERIAL PRIMARY KEY,
    props hstore
);

-- Insert sample row
INSERT INTO attributes (props)
SELECT 
  hstore(
    ARRAY[
      'color', 
      (ARRAY['red','blue','green','yellow','black'])[floor(random() * 5 + 1)],
      'size', 
      (ARRAY['S','M','L','XL'])[floor(random() * 4 + 1)]
    ]
  )
FROM generate_series(1, 500);

-- Create publication for all tables
CREATE PUBLICATION test_pub FOR ALL TABLES;

-- Create a logical replication slot
SELECT * FROM pg_create_logical_replication_slot('test_slot', 'yboutput');

-- Optional: view status
SELECT * FROM pg_replication_slots;
SELECT * FROM pg_publication;
SELECT * FROM pg_publication_tables;