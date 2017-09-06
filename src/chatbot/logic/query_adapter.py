import sys

from chatterbot.logic import LogicAdapter
from chatterbot.conversation import Statement
from textblob.classifiers import NaiveBayesClassifier
sys.path.append("/Users/jerome/Documents/garnieje/chatbot-movies/src")
from chatbot.storage import MysqlStorage

import os
import json
import spacy
import random
import re


class QueryAdapter(LogicAdapter):

    DIRECTOR = "director"

    ACTOR = "actor"

    UNKNOW = "unknow"

    PAT_DATE = re.compile("^(19|20)[0-9]{2}$")

    def __init__(self, **kwargs):
        super(QueryAdapter, self).__init__(**kwargs)
        training_file = "%s/../data/%s" % (
            os.path.dirname(os.path.realpath(__file__)),
            kwargs.get("query_training_file"))
        training_db = json.load(open(training_file))['data']
        training_data = [(sentence.lower(), int(label))
                         for label in training_db.keys() for sentence in training_db[label]]
        self.classifier = NaiveBayesClassifier(training_data)
        self.db = MysqlStorage(
            kwargs.get('host_db'),
            kwargs.get('user_db'),
            kwargs.get('password_db'),
            kwargs.get('name_db'))
        self.nlp = spacy.load('en')

    def process(self, statement):

        confidence = round(self.classifier.prob_classify(
            statement.text.lower()).prob(1), 2)
        doc = self.nlp(statement.text)

        personns = [ent for ent in doc.ents if ent.label_ == 'PERSON']
        actors = []
        director = []

        for person in personns:
            role = self.get_role(person, doc)
            if role == self.ACTOR:
                actors.append(person.text.lower())
            elif role == self.DIRECTOR:
                if len(director) > 0:
                    statement = Statement(
                        "You are asking for more than one director! Can you reformulate?")
                    statement.confidence = confidence
                    return statement
                else:
                    director.append(person.text.lower())

        dates = [ent for ent in doc.ents if ent.label_ == 'DATE']

        if len(actors) == 0 and len(director) == 0 and len(dates) == 0:
            statement = Statement(
                "You asked neither for a director, an actor, nor a date, can you reformulate?")
            statement.confidence = confidence
            return statement

        if len(dates) > 1:
            statement = Statement(
                "You asked for more than one dates, I do not understand that")
            statement.confidence = confidence
            return statement

        year = None
        if len(dates) == 1:
            year = self.validate_query_date(dates[0], doc)

        movie = self.get_movie(actors, director, year)
        movie.confidence = confidence
        return movie

    def validate_query_director(self, person, doc):

        # check left part
        if person.root.dep_ == "pobj" and person.root.head.text.lower() in ['from', 'by']:
            return True

        if person.root.dep_ == "dobj" and person.root.head.text.lower() in ['made', 'done', 'directed', 'did']:
            return True

        # check the right part: case the person is a subject
        if person.root.dep_ == "nsubj" and person.root.head.text.lower() in ['directed', 'done', 'made', 'filmed', 'did']:
            return True

        if person.root.dep_ in ['poss', 'compound']:
            for word in doc[person.end:len(doc)]:
                if word.text.lower() in ['movie', 'movies', 'film', 'films']:
                    return True

        # check the right part: case the director is at the end
        for word in doc[person.end:len(doc)]:
            if word.text.lower() == "director":
                return True

        return False

    def validate_query_actor(self, person, doc):

        if person.root.dep_ == "pobj" and person.root.head.text.lower() in ['with', 'alongside']:
            return True

        if person.root.dep_ == "dobj" and person.root.head.text.lower() in ['starring']:
            return True

        # check the right part: case the person is a subject
        if person.root.dep_ == "nsubj" and person.root.head.text.lower() in ['starred', 'stars', 'staring', 'starring', 'played', 'plays', 'playing', 'stared']:
            return True

        # case of two actors
        if person.root.dep_ == "conj" and person.root.head.tag_ == "NNP":
            return True

        # check the right part: case the director is at the end
        for word in doc[person.end:len(doc)]:
            if word.text.lower() in ["actor", "star", "actress"]:
                return True

    def validate_query_date(self, date, doc):

        if not (date.root.dep_ == "pobj" and date.root.head.text.lower() in ['from', 'in']):
            return None

        for component in date:
            if self.PAT_DATE.search(component.text):
                return component.text

        return None

    def get_role(self, person, doc):

        is_actor = self.validate_query_actor(person, doc)
        is_director = self.validate_query_director(person, doc)

        if is_actor:
            return self.ACTOR
        elif is_director:
            return self.DIRECTOR
        else:
            return self.UNKNOW

    def get_movie(self, actors, director, year):

        query, parameters = self.build_query(actors, director, year)
        cursor = self.db.get_cursor(query, tuple(parameters))
        numrows = int(cursor.rowcount)
        if numrows == 0:
            cursor.close()
            return self.build_negative_statement(actors, director, year)

        movies = []
        for row in range(numrows):
            res = cursor.fetchone()
            movies.append(res[0])
        cursor.close()
        movie = random.choice(movies)
        return self.build_positive_statement(actors, director, year, movie)

    def build_query(self, actors, director, year):

        query = "Select movie FROM Movies WHERE"
        parameters = []

        for idx, actor in enumerate(actors):
            if idx > 0:
                query += " AND"
            query += " (actor_1=%s or actor_2=%s or actor_3=%s)"
            parameters.extend([actor, actor, actor])

        if len(actors) > 0 and len(director) > 0:
            query += " AND"

        if len(director) > 0:
            query += " (director=%s)"
            parameters.append(director[0])

        if (len(actors) > 0 or len(director) > 0) and year is not None:
            query += " AND"

        if year is not None:
            query += " (year=%s)"
            parameters.append(year)

        return query, tuple(parameters)

    def build_negative_statement(self, actors, director, year):

        statement = "We do not have movies"
        names = []
        if len(actors) > 0:
            statement += " with"

        for idx, actor in enumerate(actors):
            if idx == 1:
                statement += " and"
            statement += " the actor %s"
            names.append(actor)

        if len(actors) > 0 and len(director) > 0:
            statement += " and"

        if len(director) > 0:
            statement += " from the director %s"
            names.append(director[0])

        if (len(actors) > 0 or len(director) > 0) and year is not None:
            statement += " and"

        if year is not None:
            statement += " which was released in %s"
            names.append(year)

        return Statement(statement % tuple(names))

    def build_positive_statement(self, actors, director, year, movie):

        statement = "We found the movie %s"
        names = [movie]
        if len(actors) > 0:
            statement += " with"

        for idx, actor in enumerate(actors):
            if idx == 1:
                statement += " and"
            statement += " the actor %s"
            names.append(actor)

        if len(actors) > 0 and len(director) > 0:
            statement += " and"

        if len(director) > 0:
            statement += " from the director %s"
            names.append(director[0])

        if (len(actors) > 0 or len(director) > 0) and year is not None:
            statement += " and"

        if year is not None:
            statement += " which was released in %s"
            names.append(year)

        return Statement(statement % tuple(names))


if __name__ == "__main__":

    adapter = QueryAdapter(**{
        'query_training_file': 'query_adapter_training.json',
        'host_db': 'localhost',
        'user_db': 'root',
        'password_db': "password",
        'name_db': 'imdb'
    })

    examples = [
        "A movie with both Brad Pitt and Morgan Freeman?",
        "Which movie is directed by James Cameron?",
        "A movie starring Brad Pitt?",
        "A movie by Joss Whedon with Chris Hemsworth",
        "I would like to watch a film with Tom Hardy and Christian Bale",
        "Do you know a movie where Tom Hardy stared in with Christian Bale",
        "I would like a movie where Tom Hardy is playing alongside Christian Bale",
        "A movies starring both Tom Hardy and Christian Bale",
        "I would like a movie starring Tom Hardy, Christian Bale and Joseph Gordon-Levitt",
        "A movie released in 1997",
        "A movie with Chris Hemsworth from 2013",
        "A movie directed by Sam Raimi from the year 2007",
        "A movie starring both Johnny Depp and Orlando Bloom in 2007",
        "A movie starring both Johnny Depp and Orlando Bloom in 1902",
        "A movie release in 1901"
    ]

    for example in examples:
        statement = Statement(example)
        results = adapter.process(statement)
        print("for the query {} we have the results {} with the confidence {}".format(
            statement.text, results.text, results.confidence))
