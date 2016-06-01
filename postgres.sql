psql# create role radio;
psql# alter role radio login;
psql# \password radio
Enter new password:
Enter it again:

CREATE DATABASE radio WITH OWNER = radio;

DROP TABLE programme;

CREATE TABLE programme
(
    p_id VARCHAR(36) NOT NULL
    ,p_name VARCHAR(100) NOT NULL
    ,p_download BOOLEAN NOT NULL
    ,PRIMARY KEY (p_id)
);

INSERT INTO programme (p_id, p_name, p_download) VALUES ('b01l9qb8', 'People''s Songs', TRUE);
INSERT INTO programme (p_id, p_name, p_download) VALUES ('b0100rp6', 'Radcliffe and Maconie', TRUE);
INSERT INTO programme (p_id, p_name, p_download) VALUES ('b006qpgr', 'The Archers', FALSE);

DROP TABLE programme_episode;

CREATE TABLE programme_episode
(
    pe_id VARCHAR(36) NOT NULL
    ,pe_p_id VARCHAR(36) NOT NULL
    ,pe_title VARCHAR(255) NOT NULL
    ,pe_description TEXT
    ,pe_broadcast_ts TIMESTAMP NOT NULL
    ,pe_found_ts TIMESTAMP NOT NULL
    ,pe_downloaded_ts TIMESTAMP
    ,PRIMARY KEY (pe_id)
    ,CONSTRAINT pe_p_fk FOREIGN KEY (pe_p_id) REFERENCES programme (p_id)
);

insert into programme_episode (pe_id, pe_p_id, pe_title, pe_description) VALUES ('p43h2o3', 'b0100rp6', 'John Grant', 'Fish and Chips for the Ears, with contributions from the likes of JH via GnipTwitter');


SELECT pe_id, pe_title, pe_description, pe_found_ts, pe_broadcast_ts FROM programme_episode ORDER BY pe_broadcast_ts;
SELECT pe_id, pe_title, pe_found_ts, pe_broadcast_ts FROM programme_episode ORDER BY pe_broadcast_ts;