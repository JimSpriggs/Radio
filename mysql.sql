CREATE USER 'radio'@'localhost' IDENTIFIED BY 'xxxx';

GRANT ALL PRIVILEGES ON * . * TO 'radio'@'localhost';

FLUSH PRIVILEGES;

CREATE DATABASE radio;

USE radio;

(shell command is mysql -h localhost -u radio -p radio)


DROP TABLE programme_episode;
DROP TABLE programme;
CREATE TABLE programme
(
    p_id VARCHAR(36) NOT NULL
    ,p_name VARCHAR(100) NOT NULL
    ,PRIMARY KEY (p_id)
);

INSERT INTO programme (p_id, p_name) VALUES ('b01l9qb8', 'People''s Songs');
INSERT INTO programme (p_id, p_name) VALUES ('b0100rp6', 'Radcliffe and Maconie');

CREATE TABLE programme_episode
(
    pe_id VARCHAR(36) NOT NULL
    ,pe_p_id VARCHAR(36) NOT NULL
    ,pe_title VARCHAR(255) NOT NULL
    ,pe_description TEXT
    ,PRIMARY KEY (pe_id)
    ,CONSTRAINT pe_p_fk FOREIGN KEY (pe_p_id) REFERENCES programme (p_id)
);

insert into programme_episode (pe_id, pe_p_id, pe_title, pe_description) VALUES ('p43h2o3', 'b0100rp6', 'John Grant', 'Fish and Chips for the Ears, with contributions from the likes of JH via GnipTwitter');


from mysql.connector import (connection)

cnx = connection.MySQLConnection(user='scott', password='tiger',
                                 host='127.0.0.1',
                                 database='employees')
cnx.close()