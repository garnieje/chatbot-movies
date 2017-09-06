library(readr)
library(dplyr)

data <- read.table("/Users/jerome/Documents/chatbot/data/movie_metadata.csv", 
                   strip.white=TRUE,
                   stringsAsFactors = F,
                   sep = ",",
                   comment.char = "",
                   quote = "\"",
                   header = T)
new_data <- select(data, movie_title, director_name, actor_1_name, actor_2_name, actor_3_name, title_year, language, duration, imdb_score)
new_data <- new_data %>%
  rename(movie = movie_title) %>%
  rename(director = director_name) %>%
  rename(actor_1 = actor_1_name) %>%
  rename(actor_2 = actor_2_name) %>%
  rename(actor_3 = actor_3_name) %>%
  rename(year = title_year) %>%
  rename(score = imdb_score) %>%
  mutate(director = tolower(director)) %>%
  mutate(actor_1 = tolower(actor_1)) %>%
  mutate(actor_2 = tolower(actor_2)) %>%
  mutate(actor_3 = tolower(actor_3)) %>%
  mutate(movie = substring(movie, 1, nchar(movie) - 1)) %>%
  mutate(ID = 1:n())

new_data <- select(new_data, ID, movie, director, actor_1, actor_2, actor_3, year, language, score)
  
write.table(new_data, 
            file = "/Users/jerome/Documents/chatbot/data/Movies.csv",
            sep = ",",
            qmethod = "double",
            row.names = F)
