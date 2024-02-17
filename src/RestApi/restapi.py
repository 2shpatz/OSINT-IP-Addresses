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
        # add API rules each request is handled asynchronously using asyncio.run

        @staticmethod
        @self.cache.cached(timeout=3600)  # Cache for 3600 seconds (1 hour)
        def get_ip_response(ip_addresses):
            # gets IP responses for all the given IP address (from the URL)
            try:
                ips_list = ip_addresses.split(',')
                return asyncio.run(self.get_ips_data(ips_list))
            except Exception as err:
                logging.error(err)
                return {"Error": str(err)}
            
        ############# create rules #############
        self.app.add_url_rule('/<ip_addresses>', 'get_ip_response', get_ip_response)
        ########################################
        

    def run_app(self):
        # run the flask application for listening to HTTP requests
        logging.info("starting RestApi server")
        self.add_url_rules()
        self.app.run(debug=False, host='0.0.0.0', port=self.app_port)
