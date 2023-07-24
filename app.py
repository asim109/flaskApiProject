import mysql.connector
import ast
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from urllib.parse import urlparse
import config

app = Flask(__name__)
api = Api(app)


class DNSTasks(Resource):
    domainName = config.nex_domain['windows_development']
    nexApiKey = "bac6f0f1-5ce5-4ccd-9a95-dddc8dc0e8f3"
    actions = {"True": 1, "False": 0}

    #----------------------------------------------------------------------------------------------#

    # Checking if domain name is valid. It should be ptavirata.nexlinx.net.pk
    
    def baseURLValidate(self):
        parsed_url = urlparse(request.base_url)
        domain_name = parsed_url.netloc
        return domain_name
    
    # Converting request data by PTA in dictionary.
    @classmethod
    def requestData(cls):
        data = request.get_data()
        data_str = data.decode('utf-8')
        data_dict = ast.literal_eval(data_str)
        return data_dict
    
    # Request api key validating. It should be bac6f0f1-5ce5-4ccd-9a95-dddc8dc0e8f3
    def nexAPIKeyValidate(self):
        data_dict = self.requestData()
        if data_dict['api_key'] != DNSTasks.nexApiKey:
            return {"message": "Unauthorized Request, API key is missing/invalid"}, 401
    
    # Request ID validating. It should be UNIQUE
    def requestIDValidate(self):
        data_dict = self.requestData()
        if self.find_by_request_id(data_dict['request_id']) != None:
            return {"message": "Duplicate request"}, 406
    
    # Request action validating. It should 1|0.    
    def actionValidator(self):
        data_dict = self.requestData()
        if data_dict['action'] == DNSTasks.actions["True"]:
            return DNSTasks.actions["True"]
        elif data_dict['action'] == DNSTasks.actions["False"]:
            return DNSTasks.actions["False"]
        else:
            return 501
       
    # POSTING Data in database    
    def post(self):
        try:

            if self.baseURLValidate() == DNSTasks.domainName:
                data_dict = self.requestData()
                dns_data = {'request_id': data_dict['request_id'], 'content_type': data_dict['content_type'], 'url': data_dict['url'], 'action': data_dict['action'], 'api_key': data_dict['api_key']}
                
                if data_dict['api_key'] != DNSTasks.nexApiKey:
                    return {"message": "Unauthorized Request, API key is missing/invalid"}, 401
                
                if self.actionValidator() == 501:
                    return {"message": "Invalid action"}, 501
            
                else:

                    self.insertdata_request(dns_data)
                    
                return {
                        "status": 1,
                        "responseCode": 200,
                        "message": "Operation Successful"
                        }
            else:
                return {"message": "Invalid URL"}, 500
        except Exception as e:
            print(f"A post error occured. {str(e)}")



    # Database Queries ---------------
    # Inserting data in database
    @classmethod
    def insertdata_request(self, dns_data):
        remote_ip = request.remote_addr
        request_table = "tbl_cdnsrequest"
        connectDB = mysql.connector.connect(
        host=config.database_credentials['server_ip'],
        user=config.database_credentials['db_login'],
        password=config.database_credentials['db_password'],
        database=config.database_credentials['database']
        )

        cursorObject = connectDB.cursor()
        query = f"INSERT INTO {request_table} (request_id, content_type, url, r_action, api_key, remote_addr) VALUES(%s,%s,%s,%s,%s,%s)"
        cursorObject.execute(query, (dns_data['request_id'], dns_data['content_type'], dns_data['url'], dns_data['action'], dns_data['api_key'], remote_ip))
        # #Save data in database.
        connectDB.commit()
        # #Close all connections
        cursorObject.close()
        connectDB.close()

             

api.add_resource(DNSTasks, '/api/PtaApi/DnsV20')


if __name__ == "__main__":
    app.run( port=80, debug=True, host="127.0.0.1" )
