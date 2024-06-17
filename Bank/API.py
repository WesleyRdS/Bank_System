from flask import Flask, make_response, request, jsonify, render_template, redirect, flash, session, Response
from werkzeug.serving import run_simple
import os
import threading
import json
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = "CONCORRENCIA"
IP = os.getenv("IP")

class bank:
    def __init__(self,name) -> None:
        self.name = name
        self.consortium = []
        self.transaction_queue = []
        self.agency = IP
        self.accounts = []
        self.status_transaction = "Locked"
    
    #bank informations
    def get_account(self):
        return len(self.accounts)
    
    def set_account(self,data):
        self.accounts.append(data)

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
                        if data[current_transaction['from_identificator']][itarator]['type'] == "CC":
                            data = look_for_joint_account(from_agency, from_account,'balance',data[from_identificator][itarator]['balance'])
                            save_data(data)
                        break
                break
        for client in data[current_transaction['to_identificator']]:
            if (client['agency'] == current_transaction['to_agency']) and (client['account'] == current_transaction['to_account']):
                for itarator in range(len(current_transaction['to_identificator'])):
                    if  data[current_transaction['to_identificator']][itarator]['account'] == current_transaction['to_account']:
                        data[current_transaction['to_identificator']][itarator]['balance'] = int(data[current_transaction['to_identificator']][itarator]['balance']) + int(value)
                        save_data(data)
                        if data[current_transaction['to_identificator']][itarator]['type'] == "CC":
                            data = look_for_joint_account(to_agency, to_account,'balance',data[to_identificator][itarator]['balance'])
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
                        if data[current_transaction['from_identificator']][itarator]['type'] == "CC":
                            data = look_for_joint_account(from_agency, from_account,'status','Unlocked')
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
                        if data[current_transaction['from_identificator']][itarator]['type'] == "CC":
                            data = look_for_joint_account(from_agency, from_account,'balance',data[from_identificator][itarator]['balance'])
                            save_data(data)
                            data = look_for_joint_account(from_agency, from_account,'status','Unlocked')
                            save_data(data)
                        to_att_consortium()
                        return "Transação falhou!!!"
    return "Algo deu errado"
        
def look_for_joint_account(agency, account,element,value):
    data = load_data()
    for identificator in data:
        print("Atual id:" + identificator)
        print("Atual valor:" + str(value))
        for search_cc in range(len(data[identificator])):
            if data[identificator][search_cc]['account'] == account and data[identificator][search_cc]['agency'] == agency and data[identificator][search_cc]['type'] == 'CC':
                data[identificator][search_cc][element] = value
    return data

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

def cadastrate(account, name, identificator,type_account):
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
                    'status': "Unlocked",
                    'type': type_account,
                    "session": False
                }
            ]
        }
        #Adding new cpf/cnpf in data
        data.update(new_identificator)
        #save data
        save_data(data)
        to_att_consortium()
        
        return "/account_information/Agencia: "+str(bank.get_agency())+"   Conta: "+account+"  Senha: "+generate_password(identificator)

    #if it exists
    else:
        for client in data[identificator]:
            if client['account'] == bank.get_agency():
                registered_client = True
                break
        if registered_client:
            flash("Esta conta já existe!!")
            return app.redirect('/sign_up')
        else:
            data[identificator].append({
                'name': name,
                'agency': bank.get_agency(),
                'account': account,
                'balance': 0,
                'status': "Unlocked",
                'type': type_account,
                "session": False
            })
            #save data
            save_data(data)
            to_att_consortium()
            
            return "/account_information/Agencia: "+str(bank.get_agency())+"   Conta: "+account+"  Senha: "+generate_password(identificator)

#This function has the purpose of generating a password from unique identification numbers such as cpf and cnpj
def generate_password(identificator):
    form = identificator.replace('-','.') #change the symbol - to .
    three = form.split('.')#transform the string an a array delimited by .
    group = [int(part) for part in three]
    password = []
    #Main loop that transforms groups of hundreds places starting counting from 0 into letters of the alphabet 
    for number in group:
        if 0 <= number <= 99:
            # + a number that can be 0 when dividing that number by 10 and having a whole number
            if number == 0 or number % 10 == 0:
                digit = number // 10 
            else:
                # or the remainder of the division in case of fractional results.
                digit = number % 10
            password.append(f"A{digit}")
        elif 100 <= number <= 199:
            if number == 100 or number % 10 == 0:
                digit = number // 10
            else:
                digit = number % 10
            password.append(f"B{digit}")
        elif 200 <= number <= 299:
            if number == 200 or number % 10 == 0:
                digit = number // 10
            else:
                digit = number % 10
            password.append(f"C{digit}")
        elif 300 <= number <= 399:
            if number == 300 or number % 10 == 0:
                digit = number // 10
            else:
                digit = number % 10
            password.append(f"D{digit}")
        elif 400 <= number <= 499:
            if number == 400 or number % 10 == 0:
                digit = number // 10
            else:
                digit = number % 10
            password.append(f"E{digit}")
        elif 500 <= number <= 599:
            if number == 500 or number % 10 == 0:
                digit = number // 10
            else:
                digit = number % 10
            password.append(f"F{digit}")
        elif 600 <= number <= 699:
            if number == 600 or number % 10 == 0:
                digit = number // 10
            else:
                digit = number % 10
            password.append(f"G{digit}")
        elif 700 <= number <= 799:
            if number == 700 or number % 10 == 0:
                digit = number // 10
            else:
                digit = number % 10
            password.append(f"H{digit}")
        elif 800 <= number <= 899:
            if number == 800 or number % 10 == 0:
                digit = number // 10
            else:
                digit = number % 10
            password.append(f"I{digit}")
        elif 900 <= number <= 999:
            if number == 900 or number % 10 == 0:
                digit = number // 10
            else:
                digit = number % 10
            password.append(f"J{digit}")
    #return a string formed by adding array items
    return ''.join(password)

def account_generate():
    num = bank.get_account()
    form = bank.get_agency().replace('.',str(num))
    bank.set_account(form)
    return form

#Main page
@app.route('/')
def login_page():
    if 'logged_in' in session:
        return app.redirect('/home')
    return render_template('login.html')

@app.route('/home')
def home():
    if 'logged_in' in session:
        return session['cpf']
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    data = load_data()
    if 'logged_in' in session:
        for logout in range(len(data[session['cpf']])):
            if data[session['cpf']][logout]["account"] == session['account'] and data[session['cpf']][logout]["agency"] == session['agency']:
                data[session['cpf']][logout]["session"] = False
                save_data(data)
                to_att_consortium()
        session.pop('logged_in', None)
        session.pop('cpf', None)
        session.pop('account', None)
        session.pop('agency', None)
        return render_template('login.html')
    else:
        return render_template('login.html')

#login route
@app.route('/login', methods=['POST'])
def login():
    agency = request.form.get('agency')
    account = request.form.get('account')
    password = request.form.get('password')
    data = load_data()
    for itarator in data:
        pass_password = generate_password(itarator)
        if pass_password == password:#check if the primarykey transformation generate this password
            for check in data[itarator]:
                if check['account'] == account and check['agency'] == agency and check['session'] == False:#search account
                    session['cpf'] = itarator
                    session['account'] = check['account'] 
                    session['agency'] = check["agency"]
                    session['logged_in'] = True
                    for index in range(len(data[itarator])):
                        if data[itarator][index]['account'] == account and data[itarator][index]['agency'] == agency:
                            data[itarator][index]['session'] = True
                            save_data(data)
                            to_att_consortium()
                    return app.redirect('/home')
                elif check['session'] == True:
                    flash("Esta conta ja se encontra logada em outro dispositivo!!!")
    flash("Conta, agência ou senha invalidos!!!")
    return app.redirect('/')

#route to atualizate the consortium data for the others banks
@app.route('/from_att_consortium')
def from_att_consortium():
    data = request.get_json() #receive post menssages from the others banks
    save_data(data)
    return bank.get_agency()

@app.route('/sign_up')
def sign_up():
    return render_template('sign_up.html')


@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form.get('client')
    agency = request.form.get('agency')
    identifier = request.form.get('identifier')
    if identifier == "cpf":
        cpf = request.form.get('cpf')
        type_account = request.form.get('type_account')
        if type_account == "CC":
            cpf_cc = cpf
            aux_cpf = request.form.get('cpf1')
            aux_name = request.form.get('client1')
            index = 1
            while aux_cpf != None:
                cpf_cc = cpf_cc+'@'+aux_cpf
                name = name+'@'+aux_name
                index += 1
                aux_cpf = request.form.get('cpf'+str(index))  
            account = account_generate()
            return app.redirect("http://"+agency+':9985/sign_up/'+account+"/"+name+"/"+cpf_cc+"/"+type_account)
        else:
            pass
    else:
        pass
    return identifier

@app.route("/account_information/<data>")
def account_information_singup(data):
    response = Response(
        data,
        content_type='text/plain',
    )
    # Nome do arquivo sugerido para download
    response.headers['Content-Disposition'] = 'attachment; filename=account_information.txt'

    return response

#create new account route
@app.route('/sign_up/<account>/<name>/<identificator>/<type_account>')
def sign_up_manager(account, name, identificator,type_account):
    list_singup = []
    if type_account == "CC":
        array_counts = identificator.split('@')
        name_counts = name.split('@')
        for primaryKey, nameKey in zip(array_counts,name_counts):
            output = cadastrate(account, nameKey, primaryKey,type_account)
            list_singup.append(output)
        return app.redirect(list_singup[0])
            
                
    else:
        return cadastrate(account, name, identificator,type_account)


#direct deposit route 
@app.route("/deposit/<agency>/<account>/<identificator>/<value>")
def deposit(agency, account, identificator,value):
    if 'logged_in' in session:
        data = load_data()
        for acc in range(0,len(data[identificator])):
            in_data = data[identificator][acc] #banks account getter 
            #verify if a client is the targent searched
            if (in_data['agency'] == agency) and (in_data['account'] == account):
                data[identificator][acc]['balance'] = int(in_data['balance']) + int(value)
                if in_data['type'] == "CC":
                    data = look_for_joint_account(agency, account,'balance',data[identificator][acc]['balance'])

                save_data(data)
                to_att_consortium()
                return "Foi depoisitado R$" + value + " na sua conta -- Agencia: " + agency 
        return "Esta conta não existe"
    else:
        return render_template('login.html')

@app.route('/transfer/<from_identificator>/<from_agency>/<from_account>/<to_identificator>/<to_agency>/<to_account>/<value>')
def check_balance(from_identificator,from_agency, from_account, 
                              to_identificator, to_agency, to_account, value):
    if 'logged_in' in session:
        data = load_data()
        for client in data[from_identificator]:
            if client['account'] == from_account:
                balance = int(client['balance']) - int(value)
                if balance >= 0 and client['status'] == 'Unlocked':
                    for search in range(len(data[from_identificator])):
                        if data[from_identificator][search]['account'] == from_account:
                            data[from_identificator][search]['status'] = "Locked"
                            if data[from_identificator][search]['type'] == "CC":
                                data = look_for_joint_account(from_agency, from_account,'status','Locked')
                                save_data(data)
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
    else:
        return render_template('login.html')
if __name__ == "__main__":
    bank = bank("A")
    run_simple(IP, 9985, app)