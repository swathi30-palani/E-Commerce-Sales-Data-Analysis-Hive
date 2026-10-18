-- Run once in Hive (beeline / Hive CLI):  beeline -u jdbc:hive2://localhost:10000 -n hive -f setup_hive.sql
CREATE DATABASE IF NOT EXISTS ecommerce;

CREATE TABLE IF NOT EXISTS ecommerce.sales (
  order_id       INT,
  order_date     DATE,
  product        STRING,
  category       STRING,
  quantity       INT,
  price          DOUBLE,
  region         STRING,
  payment_method STRING
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE;

-- Sample rows (skip if your table already has data)
INSERT INTO TABLE ecommerce.sales VALUES
 (1001,'2026-09-01','Wireless Mouse','Electronics',2,499.00,'South','UPI'),
 (1002,'2026-09-02','Running Shoes','Fashion',1,2499.00,'North','Card'),
 (1003,'2026-09-03','Coffee Maker','Home',1,3299.00,'West','Cash'),
 (1004,'2026-09-04','Notebook Pack','Stationery',5,150.00,'East','UPI');
