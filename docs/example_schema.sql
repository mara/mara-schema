DROP SCHEMA IF EXISTS e_dim CASCADE;
CREATE SCHEMA e_dim;

CREATE TYPE e_dim.STATUS AS ENUM ('New', 'In process', 'Closed');

DROP TABLE IF EXISTS e_dim.order CASCADE;
CREATE TABLE e_dim.order (
  order_id    INTEGER PRIMARY KEY,
  customer_fk INTEGER,
  order_date  TIMESTAMP WITH TIME ZONE,
  status      e_dim.STATUS
);

DROP TABLE IF EXISTS e_dim.order_item CASCADE;
CREATE TABLE e_dim.order_item (
  order_item_id INTEGER PRIMARY KEY,
  order_fk      INTEGER,
  product_fk    INTEGER,
  revenue     DOUBLE PRECISION
);

DROP TABLE IF EXISTS e_dim.customer CASCADE;
CREATE TABLE e_dim.customer (
  customer_id                     INTEGER PRIMARY KEY,
  first_order_fk                  INTEGER,
  age                             INTEGER,
  duration_since_first_order_days INTEGER,
  number_of_orders                INTEGER,
  revenue_lifetime                DOUBLE PRECISION
);

DROP TABLE IF EXISTS e_dim.product CASCADE;
CREATE TABLE e_dim.product (
  product_id       INTEGER PRIMARY KEY,
  categories       TEXT [],
  revenue_all_time DOUBLE PRECISION
);

ALTER TABLE e_dim.order
  ADD FOREIGN KEY (customer_fk) REFERENCES e_dim.customer (customer_id);
ALTER TABLE e_dim.order_item
  ADD FOREIGN KEY (order_fk) REFERENCES e_dim.order (order_id);
ALTER TABLE e_dim.order_item
  ADD FOREIGN KEY (product_fk) REFERENCES e_dim.product (product_id);
ALTER TABLE e_dim.customer
  ADD FOREIGN KEY (first_order_fk) REFERENCES e_dim.order (order_id);
