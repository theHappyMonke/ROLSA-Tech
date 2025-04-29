DROP TABLE products; --Deleted this table because I needed to add a new field "image" that I forgot.

DROP TABLE carbonFootprintCalculation; --Deleted this table because I needed to add new fields for each data field I wanted to store.
DROP TABLE energyCalculation; --Deleted this table because I needed to add new fields for each data field I wanted to store.

INSERT INTO productTypes (name) VALUES ("Solar panels");
INSERT INTO productTypes (name) VALUES ("Electric vehicle chargers");
INSERT INTO productTypes (name) VALUES ("Energy management systems");

INSERT INTO products (name, description, origin, image, typeID) VALUES ("Solar panel", "It takes in the sun", "some website", "no image", 1);
INSERT INTO products (name, description, origin, image, typeID) VALUES ("Electric vehicle charger", "Charges electric vehicles", "some website", "no image", 2);
INSERT INTO products (name, description, origin, image, typeID) VALUES ("Energy management systems", "Helps manage energy", "some website", "no image", 3);