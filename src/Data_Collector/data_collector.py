import os
import logging
import requests
import json
import asyncio
from enum import Enum
from flask import jsonify
from flask_caching import Cache

from ipaddress import ip_address

logging.basicConfig(level=logging.INFO)


class IP_RESP_FIELDS(Enum):
    METRICS = "metrics"
    RAW_DATA = "raw_data"
    STATUS = "status"
    TIME = "time"
    TOTAL = "total"


class DataCollector():
    def __init__(self) -> None:
        
        self.default_headers = {'accept': 'application/json'}
        
        if "IP_APIS" in os.environ:
            self.ip_apis = json.loads(os.getenv("IP_APIS"))
        else:
            # set default IP APIs
            self.ip_apis = {
                "ip-api" : {"url": "http://ip-api.com/json", "resp_time": 1},
                "bgview": {"url": "https://api.bgpview.io/ip", "resp_time": 2},
            }

        

    async def get_request_handler(self, req:str) -> (requests.Response | None):
        # handle the requests.get commands and returns the response
        try:
            response = requests.get(req, headers=self.default_headers)
            await asyncio.sleep(1)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.HTTPError as err:
            logging.error("HTTP error occurred:%s", err)
            return None
        except requests.exceptions.ConnectionError as err:
            logging.error("Error connecting:%s", err)
            return None
        except requests.exceptions.Timeout as err:
            logging.error("Request timed out:%s", err)
            return None
        except requests.exceptions.RequestException as err:
            logging.error("Request exception occurred:%s", err)
            return None
        except ValueError as err:
            logging.error("Error parsing JSON:", err)
            return None
        except Exception as err:
            logging.critical("Unknown Error:", err)
            raise

    async def get_ip_server_data(self, url, ip):
        ip_server_data = await self.get_request_handler(f'{url}/{ip}')
        logging.info("get_ip_server_data return: %s", ip_server_data)
        return ip_server_data

    async def create_ip_response(self, ip):
        try:
            ip_address(ip)
        except ValueError as err:
            logging.error("IP: {ip} is not valid: ", err)
            return {"Error": str(err)}

        logging.info(f"create ip response for {ip}")
        ip_resp = {IP_RESP_FIELDS.METRICS.value: {}, IP_RESP_FIELDS.RAW_DATA.value: {}}
        failure = False
        total_time = 0
        for ip_server_name, server_params in self.ip_apis.items():
            logging.info("Handling server %s with params %s", ip_server_name, server_params)
            ip_server_data = await self.get_ip_server_data(server_params.get("url") ,ip)
            total_time += server_params.get("resp_time")
            if ip_server_data is not None:
                ip_resp[IP_RESP_FIELDS.METRICS.value][ip_server_name] = { IP_RESP_FIELDS.STATUS.value: "success", IP_RESP_FIELDS.TIME.value: server_params.get("resp_time")}
                ip_resp[IP_RESP_FIELDS.RAW_DATA.value][ip_server_name] = ip_server_data
            else: 
                ip_resp[IP_RESP_FIELDS.METRICS.value][ip_server_name] = { IP_RESP_FIELDS.STATUS.value: "failure", IP_RESP_FIELDS.TIME.value: server_params.get("resp_time")}
                ip_resp[IP_RESP_FIELDS.RAW_DATA.value][ip_server_name] = {"N/A"}
                failure = True

        if failure:
            ip_resp[IP_RESP_FIELDS.METRICS.value][IP_RESP_FIELDS.TOTAL.value] = {IP_RESP_FIELDS.STATUS.value: "failure", IP_RESP_FIELDS.TIME.value: total_time}
        ip_resp[IP_RESP_FIELDS.METRICS.value][IP_RESP_FIELDS.TOTAL.value] = {IP_RESP_FIELDS.STATUS.value: "success", IP_RESP_FIELDS.TIME.value: total_time}

        return jsonify(ip_resp)
