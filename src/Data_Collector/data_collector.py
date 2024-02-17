import os
import logging
import requests
import json
import asyncio
from enum import Enum
from flask import jsonify
from flask_caching import Cache

from ipaddress import ip_address

# logging.basicConfig(level=logging.DEBUG)


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
        logging.info("Using these IP APIs %s", self.ip_apis)
        

    async def _get_request_handler(self, req:str) -> (requests.Response | None):
        # handle the requests.get commands and returns the response
        try:
            response = requests.get(req, headers=self.default_headers)
            await asyncio.sleep(1)
            response.raise_for_status()
            data = response.json()
            logging.debug("get_request_handler return: %s", data)
            return data
        except requests.exceptions.HTTPError as err:
            logging.error("HTTP error occurred:%s", err)
            raise
        except requests.exceptions.ConnectionError as err:
            logging.error("Error connecting:%s", err)
            raise
        except requests.exceptions.Timeout as err:
            logging.error("Request timed out:%s", err)
            raise
        except requests.exceptions.RequestException as err:
            logging.error("Request exception occurred:%s", err)
            raise
        except ValueError as err:
            logging.error("Error parsing JSON:", err)
            raise
        except Exception as err:
            logging.critical("Unknown Error:", err)
            raise


    async def get_ips_data(self, ip_addresses):
        # Collects ip data for all the given IP addresses
        try:
            logging.info("Received these ip addresses: %s", ip_addresses)
            for ip in ip_addresses:
                ip_address(ip)
        except ValueError as err:
            logging.error(f"IP: {ip} is not valid")
            return {"Error": str(err)}
        ips_data_list = []
        for ip in ip_addresses:
            ips_data_list.append(await self._create_ip_response(ip))
        return jsonify(ips_data_list)


    async def _create_ip_response(self, ip):
        # create ip JSON response for a given IP address
        logging.info(f"create ip response for {ip}")
        ip_resp = {IP_RESP_FIELDS.METRICS.value: {}, IP_RESP_FIELDS.RAW_DATA.value: {}}
        failure = False
        total_time = 0
        for ip_server_name, server_params in self.ip_apis.items():
            logging.debug("Handling server %s with params %s", ip_server_name, server_params)
            get_request_url = os.path.join(server_params.get("url") ,ip)
            try:
                ip_server_data = await self._get_request_handler(get_request_url)
                ip_resp[IP_RESP_FIELDS.METRICS.value][ip_server_name] = { IP_RESP_FIELDS.STATUS.value: "success", IP_RESP_FIELDS.TIME.value: server_params.get("resp_time")}
                ip_resp[IP_RESP_FIELDS.RAW_DATA.value][ip_server_name] = ip_server_data
            
            except Exception as err:
                logging.error("get_ip_server_data: %s", err)
                ip_resp[IP_RESP_FIELDS.METRICS.value][ip_server_name] = { IP_RESP_FIELDS.STATUS.value: "failure", IP_RESP_FIELDS.TIME.value: server_params.get("resp_time")}
                ip_resp[IP_RESP_FIELDS.RAW_DATA.value][ip_server_name] = {"Error": str(err)}
                failure = True

            total_time += server_params.get("resp_time")                

        if failure:
            ip_resp[IP_RESP_FIELDS.METRICS.value][IP_RESP_FIELDS.TOTAL.value] = {IP_RESP_FIELDS.STATUS.value: "failure", IP_RESP_FIELDS.TIME.value: total_time}
        ip_resp[IP_RESP_FIELDS.METRICS.value][IP_RESP_FIELDS.TOTAL.value] = {IP_RESP_FIELDS.STATUS.value: "success", IP_RESP_FIELDS.TIME.value: total_time}
        logging.debug("create_ip_response returns: %s", ip_resp )
        return ip_resp
