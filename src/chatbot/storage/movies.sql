CREATE TABLE `Movies` (
	`ID` int(11) unsigned NOT NULL,
	`movie` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
	`director` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
	`actor_1` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
	`actor_2` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
	`actor_3` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
	`year` int(11) unsigned DEFAULT 0,
	`language` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
	`score` float(1) DEFAULT NULL,
	PRIMARY KEY (`ID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci ROW_FORMAT=COMPRESSED;

LOAD DATA LOCAL INFILE "/Users/jerome/Documents/chatbot/data/Movies.csv"
INTO TABLE Movies
COLUMNS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
ESCAPED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES;