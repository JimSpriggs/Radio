create role radio;
alter role radio login;

connect as radio

\password radio
Enter new password:
Enter it again:

CREATE DATABASE radio WITH OWNER = radio;

psql --dbname=radio --username=radio

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
INSERT INTO programme (p_id, p_name, p_download) VALUES ('b07tczl3', 'The Matter of the North', TRUE);


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

INSERT INTO public.programme_episode (pe_id, pe_p_id, pe_title, pe_description, pe_broadcast_ts, pe_found_ts, pe_downloaded_ts) VALUES ('b075qbnj', 'b0100rp6', 'John Niven', 'Stuart and Mark''s guest today is the cult author and journalist John Niven. Well-known for his novels such as Kill Your Friends and Cold Hands (both of which are currently being adapted for film), he''s here to talk about his new book. Plus attempt to get your dulcet tones on the DAB airwaves by suggesting what track follows what, in trusty all-round good egg The Chain - or gather your friends around the wireless for some Teatime Themetime fun times by guessing the link between three records. What ARE you waiting for?!', '2016-04-11 13:00:00.000000', '2016-05-09 21:57:25.150222', '2016-05-10 22:29:38.919056');

SELECT pe_id, pe_title, pe_description, pe_found_ts, pe_broadcast_ts FROM programme_episode ORDER BY pe_broadcast_ts;
SELECT pe_id, pe_title, pe_found_ts, pe_broadcast_ts FROM programme_episode ORDER BY pe_broadcast_ts;