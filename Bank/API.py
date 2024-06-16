from flask import Flask, make_response, request, jsonify
from werkzeug.serving import run_simple
import os
import threading
import json
import requests

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
IP = os.getenv("IP")

class bank:
    def __init__(self,name) -> None:
        self.name = name
        self.consortium = []
        self.transaction_queue = []
        self.agency = IP
        self.status_transaction = "Locked"
    
    #bank informations
    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name
    
    def get_agency(self):
        return self.agency
    
    def set_status(self,status):
        self.status_transaction = status

    def get_status(self):
        return self.status_transaction

    #Adding transactions to a queue in case of concurrent transactions
    def set_transaction_queue(self, transaction):
        self.transaction_queue.append(transaction)

    def get_transaction_queue(self):
        return self.transaction_queue
    
    def get_next_transaction_queue(self):
        return self.transaction_queue.pop()


#Data Access
def load_data():
    try:
        with open('consorcio.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}
    return data

def save_data(data):
    with open('consorcio.json', 'w') as file:
        json.dump(data, file)


def send_value_to_destination(from_identificator,from_agency, from_account, 
                              to_identificator, to_agency, to_account, value):
    data = load_data()
    response = ''
    new_transaction = {
                    'from_identificator': from_identificator,
                    'from_agency': from_agency,
                    'from_account': from_account,
                    'to_identificator': to_identificator,
                    'to_agency': to_agency,
                    'to_account': to_account,
                    'value': value
                }
        
    bank.set_transaction_queue(new_transaction)
    while(len(bank.get_transaction_queue()) != 0):
        current_transaction = bank.get_next_transaction_queue()
        for client in data[current_transaction['from_identificator']]:
            if (client['agency'] == current_transaction['from_agency']) and (client['account'] == current_transaction['from_account']):
                for itarator in range(len(current_transaction['from_identificator'])):
                    if  data[current_transaction['from_identificator']][itarator]['account'] == current_transaction['from_account']:
                        data[current_transaction['from_identificator']][itarator]['balance'] = int(data[current_transaction['from_identificator']][itarator]['balance']) - int(value)
                        save_data(data)
                        break
                break
        for client in data[current_transaction['to_identificator']]:
            if (client['agency'] == current_transaction['to_agency']) and (client['account'] == current_transaction['to_account']):
                for itarator in range(len(current_transaction['to_identificator'])):
                    if  data[current_transaction['to_identificator']][itarator]['account'] == current_transaction['to_account']:
                        data[current_transaction['to_identificator']][itarator]['balance'] = int(data[current_transaction['to_identificator']][itarator]['balance']) + int(value)
                        save_data(data)
                        response = to_att_consortium()
                        break
                break
        for check_response in response:
            if check_response == current_transaction['to_agency']:
                for itarator in range(len(current_transaction['from_identificator'])):
                    if  data[current_transaction['from_identificator']][itarator]['account'] == current_transaction['from_account']:
                        data[current_transaction['from_identificator']][itarator]['status'] = 'Unlocked'
                        save_data(data)
                        to_att_consortium()
                        return "Transação realizada com sucesso!!!"
                
    
        for client in data[current_transaction['from_identificator']]:
            if (client['agency'] == current_transaction['from_agency']) and (client['account'] == current_transaction['from_account']) and (client['status'] == "Locked"):
                for itarator in range(len(current_transaction['from_identificator'])):
                    if  data[current_transaction['from_identificator']][itarator]['account'] == current_transaction['from_account']:
                        data[current_transaction['from_identificator']][itarator]['balance'] = int(data[current_transaction['from_identificator']]['balance']) + int(value)
                        data[current_transaction['from_identificator']][itarator]['status'] = 'Unlocked'
                        save_data(data)
                        to_att_consortium()
                        return "Transação falhou!!!"
    return "Algo deu errado"
        





#Send atualized consortium data from the others banks
def to_att_consortium():
    consortium_list = load_data()
    response_list = []
    for identificator in consortium_list:
        for consortium in consortium_list[identificator]:
            if consortium['agency'] != bank.get_agency():
                #building a dynamic route
                url_destination = "http://"+consortium['agency']+":9985/from_att_consortium"
                print("Esperando resposta de: "+consortium['agency'])
                try:
                    #try make a request in the route
                    response = requests.post(url_destination, json=consortium_list)
                    response_list.append(response.text)
                except ConnectionError:
                    response_list.append("Erro de conexão")
                except TimeoutError:
                    response_list.append("Erro de tempo de resposta")
                except:
                    response_list.append("Erro desconhecido")
            else:
                response_list.append(bank.get_agency())
    return response_list

#route to atualizate the consortium data for the others banks
@app.route('/from_att_consortium')
def from_att_consortium():
    data = request.get_json() #receive post menssages from the others banks
    save_data(data)
    return bank.get_agency()

#create new account route
@app.route('/sing_up/<account>/<name>/<identificator>')
def sing_up_manager(account, name, identificator):
    data = load_data()
    registered_client = False
    if identificator not in data: #checking if the CPF/CNPJ does not exists in the file
        new_identificator = {
            identificator: [
                {
                    'name': name,
                    'agency': bank.get_agency(),
                    'account': account,
                    'balance': 0,
                    'status': "Unlocked"
                }
            ]
        }
        #Adding new cpf/cnpf in data
        data.update(new_identificator)
        #save data
        save_data(data)
        to_att_consortium()
        return "Cliente cadastrado com sucesso"

    #if it exists
    else:
        for client in data[identificator]:
            if client['account'] == bank.get_agency():
                registered_client = True
                break
        if registered_client:
            return "Cliente já cadastrado"
        else:
            data[identificator].append({
                'name': name,
                'agency': bank.get_agency(),
                'account': account,
                'balance': 0,
                'status': "Unlocked"
            })
            #save data
            save_data(data)
            to_att_consortium()
            return "Cliente cadastrado com sucesso"

#direct deposit route 
@app.route("/deposit/<agency>/<account>/<identificator>/<value>")
def deposit(agency, account, identificator,value):
    data = load_data()
    for conta in range(0,len(data[identificator])):
        in_data = data[identificator][conta] #banks account getter 
        #verify if a client is the targent searched
        if (in_data['agency'] == agency) and (in_data['account'] == account):
            data[identificator][conta]['balance'] = int(in_data['balance']) + int(value)
            save_data(data)
            to_att_consortium()
            return "Foi depoisitado R$" + value + " na sua conta -- Agencia: " + agency 
    return "Esta conta não existe"


@app.route('/transfer/<from_identificator>/<from_agency>/<from_account>/<to_identificator>/<to_agency>/<to_account>/<value>')
def check_balance(from_identificator,from_agency, from_account, 
                              to_identificator, to_agency, to_account, value):
    data = load_data()
    for client in data[from_identificator]:
        if client['account'] == from_account:
            balance = int(client['balance']) - int(value)
            if balance >= 0 and client['status'] == 'Unlocked':
                for search in range(len(data[from_identificator])):
                    if data[from_identificator][search]['account'] == from_account:
                        data[from_identificator][search]['status'] = "Locked"
                save_data(data)
                return send_value_to_destination(from_identificator,from_agency, from_account, 
                              to_identificator, to_agency, to_account, value)
            elif client['status'] == "Locked":
                new_transaction = {
                    'from_identificator': from_identificator,
                    'from_agency': from_agency,
                    'from_account': from_account,
                    'to_identificator': to_identificator,
                    'to_agency': to_agency,
                    'to_account': to_account,
                    'value': value
                }
        
                bank.set_transaction_queue(new_transaction)
                return send_value_to_destination(from_identificator,from_agency, from_account, 
                              to_identificator, to_agency, to_account, value)
            else:
                return "Saldo insuficiente!!"
    return "Destino não encontrado!"
if __name__ == "__main__":
    bank = bank("A")
    run_simple(IP, 9985, app)