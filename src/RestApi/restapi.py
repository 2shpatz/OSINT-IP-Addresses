import os
import logging
from flask import Flask, jsonify
from Data_Collector.data_collector import DataCollector
logging.basicConfig(level=logging.INFO)

class App(DataCollector):
    def __init__(self, port=os.getenv("APP_PORT")) -> None:
        super().__init__()
        self.app = Flask(__name__)
        self.app_port = port

    def add_url_rules(self):
        # add API rules 
        self.app.add_url_rule('/<ip>', 'create_ip_response', self.create_ip_response)
    
    def run_app(self):
        # run the flask application for listening to HTTP requests
        logging.info("starting RestApi server")
        self.add_url_rules()
        self.app.run(debug=True, port=self.app_port)