import sys

from chatterbot.logic import LogicAdapter
from chatterbot.conversation import Statement
from textblob.classifiers import NaiveBayesClassifier
sys.path.append("/Users/jerome/Documents/garnieje/chatbot/src")
from chatbot.storage import MysqlStorage

import os
import json
import spacy
import random


class QueryAdapter(LogicAdapter):

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

        if len(personns) == 0:
            statement = Statement("You don't give me any name!")
            statement.confidence = confidence
            return statement
        elif len(personns) > 1:
            statement = Statement("You give me more than one name!")
            statement.confidence = confidence
            return statement

        person = personns[0]
        valid = self.validate_query_director(person, doc)

        if not valid:
            statement = Statement(
                "It doesn't look like you are asking for a director, can you reformulate?")
            statement.confidence = confidence
            return statement

        movie = self.get_movie(person.text.lower())
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


    def get_movie(self, name):

        query = "Select movie FROM Movies WHERE director=%s"
        cursor = self.db.get_cursor(query, (name, ))
        numrows = int(cursor.rowcount)
        if numrows == 0:
            cursor.close()
            return Statement("We do not have movies from the director %s" % name)

        movies = []
        for row in range(numrows):
            res = cursor.fetchone()
            movies.append(res[0])
        cursor.close()
        movie = random.choice(movies)
        return Statement("We found the movie %s from the director %s" % (movie, name))

if __name__ == "__main__":

    adapter = QueryAdapter(**{
        'query_training_file': 'query_adapter_training.json',
        'host_db': 'localhost',
        'user_db': 'root',
        'password_db': "password",
        'name_db': 'imdb'
    })

    examples = [
        "Which movie is directed by James Cameron?",
        "What movie has made James Cameron?",
        "what are James Cameron movies?",
        "Can you give me one movie by James Cameron",
        "Do you know one film from James Cameron?",
        "A movie by James Cameron",
        "A film from James Cameron",
        "Do you have a work by James Cameron",
        "A piece of work from James Cameron",
        "I would like a movie from James Cameron",
        "is there a film by James Cameron",
        "Anything by James Cameron?",
        "Which movie has James Cameron as director?",
        "A film with James Cameron as director",
        "Film directed by James Cameron",
        "Movie directed by James Cameron"
    ]

    for example in examples:
        statement = Statement(example)
        confidence, title = adapter.process(statement)
        print("for the query {} we have the results {} with the confidence {}".format(
            statement.text, title, confidence))
