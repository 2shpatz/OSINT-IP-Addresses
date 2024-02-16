import os
import logging
from flask import Flask, jsonify
from flask_caching import Cache
import asyncio

from Data_Collector.data_collector import DataCollector

logging.basicConfig(level=logging.INFO)

class App(DataCollector):
    def __init__(self, port=os.getenv("APP_PORT")) -> None:
        super().__init__()
        self.app_port = port
        
        self.app = Flask(__name__)
        self.cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
        self.cache.init_app(self.app)

    def add_url_rules(self):
        # add API rules 
        @staticmethod
        @self.cache.cached(timeout=3600)  # Cache for 3600 seconds (1 hour)
        def get_ip_response(ip):
            return asyncio.run(self.create_ip_response(ip))
        
        self.app.add_url_rule('/<ip>', 'get_ip_response', get_ip_response)
        

    def run_app(self):
        # run the flask application for listening to HTTP requests
        logging.info("starting RestApi server")
        self.add_url_rules()
        self.app.run(debug=True, host='0.0.0.0', port=self.app_port)
