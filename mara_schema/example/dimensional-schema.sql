DROP SCHEMA IF EXISTS dim CASCADE;
CREATE SCHEMA dim;

CREATE TYPE dim.STATUS AS ENUM ('New', 'Paid', 'Shipped', 'Returned', 'Refunded');

CREATE TABLE dim.order
(
    order_id    INTEGER PRIMARY KEY,
    customer_fk INTEGER    NOT NULL,
    order_date  TIMESTAMP WITH TIME ZONE,
    status      dim.STATUS NOT NULL
);

CREATE TABLE dim.order_item
(
    order_item_id    INTEGER PRIMARY KEY,
    order_fk         INTEGER          NOT NULL,
    product_fk       INTEGER          NOT NULL,

    product_revenue  DOUBLE PRECISION NOT NULL,
    shipping_revenue DOUBLE PRECISION NOT NULL
);

CREATE TABLE dim.customer
(
    customer_id                   INTEGER PRIMARY KEY,
    email                         TEXT NOT NULL,
    duration_since_first_order    INTEGER,
    first_order_fk                INTEGER,
    favourite_product_category_fk INTEGER,

    number_of_orders              INTEGER,
    revenue_lifetime              DOUBLE PRECISION
);

CREATE TABLE dim.product
(
    product_id          INTEGER PRIMARY KEY,
    sku                 TEXT    NOT NULL,
    product_category_fk INTEGER NOT NULL,
    revenue_all_time    DOUBLE PRECISION
);

CREATE TABLE dim.product_category
(
    product_category_id INTEGER PRIMARY KEY,
    level_1             TEXT NOT NULL,
    level_2             TEXT NOT NULL
);


ALTER TABLE dim.order
    ADD FOREIGN KEY (customer_fk) REFERENCES dim.customer (customer_id);
ALTER TABLE dim.order_item
    ADD FOREIGN KEY (order_fk) REFERENCES dim.order (order_id);
ALTER TABLE dim.order_item
    ADD FOREIGN KEY (product_fk) REFERENCES dim.product (product_id);
ALTER TABLE dim.customer
    ADD FOREIGN KEY (first_order_fk) REFERENCES dim.order (order_id);
ALTER TABLE dim.customer
    ADD FOREIGN KEY (favourite_product_category_fk)
        REFERENCES dim.product_category (product_category_id);
ALTER TABLE dim.product
    ADD FOREIGN KEY (product_category_fk) REFERENCES dim.product_category (product_category_id);