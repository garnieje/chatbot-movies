from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import logging
logging.basicConfig(level=logging.INFO)

import sys
sys.path.append("/Users/jerome/Documents/garnieje/chatbot/src")

bot = ChatBot(
    "Jerome_naive",
    storage_adapter="chatterbot.storage.JsonFileStorageAdapter",
    input_adapter='chatterbot.input.TerminalAdapter',
    output_adapter='chatterbot.output.TerminalAdapter',
    logic_adapters=[
        'chatbot.logic.query_adapter.QueryAdapter',
        'chatterbot.logic.BestMatch'
    ],
    database="../database/naive_db.db",
    query_training_file="../data/query_adapter_training.json",
    host_db='localhost',
    user_db='root',
    password_db='password',
    name_db='imdb'
)

bot.set_trainer(ChatterBotCorpusTrainer)
bot.train(
    "chatterbot.corpus.english.greetings",
    "chatterbot.corpus.english.conversations"
)

print("The bot is ready")
while True:
    try:
     bot_input = bot.get_response(None)

    except(KeyboardInterrupt, EOFError, SystemExit):
        break


