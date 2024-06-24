from flask import Flask, request, redirect, session, jsonify
import urllib.request, json
import sqlite3
from openai import OpenAI

app = Flask(__name__)
app.secret_key = 'ABCDE'

client = OpenAI(api_key="XXX")

conn = sqlite3.connect("/opt/flask-app/DB/Chatbot.db", check_same_thread=False)
cur = conn.cursor()

userinput = ''
UserID = ''
ShowLog = ''
Regis_message = ''
Error_Code = False
@app.route('/Check', methods={'GET', 'POST'})
def index():
        return 'Connected'

@app.route('/Login', methods={'GET', 'POST'})
def Login():
        global UserID, Error_Code, ChatLog
        if request.method == 'POST':
                UserID = request.args.get('ID')
                UserPW = request.args.get('PW')
                Sql = "Select UserPW From User Where UserID = '{0}'".format(UserID)
                cur.execute(Sql)
                myresult = cur.fetchone()
                if myresult:
                        if str(UserPW) == myresult[0]:
                                Error_Code = False
                                Sql = "Select Sum From UserSum Where UserID = '{0}'".format(UserID)
                                cur.execute(Sql)
                                myresult = cur.fetchone()
                                if myresult[0] == '':
                                        ChatLog = ', and now you are serveing a new user.'
                                else:
                                        ChatLog = myresult[0]
                                return jsonify({'response': 'Login success'})
                        else:
                                Error_Code = True
                else:
                        Error_Code  = True

        if request.method == 'GET':
                if Error_Code == True:
                        Response = 'Wrong ID or Password, please login again!'
                elif UserID == '':
                        Response = 'Please Login!'
                else:
                        Response = 'Login success'
                return jsonify(Response)

@app.route('/Regis', methods={'GET', 'POST'})
def Regis():
        global Regis_message
        if request.method == 'POST':
                UserID = request.args.get('ID')
                UserPW = request.args.get('PW')
                if UserID != '' and UserPW != '':
                        Sql = "Select * From User Where UserID = '{0}'".format(UserID)
                        cur.execute(Sql)
                        myresult = cur.fetchone()
                        if myresult:
                                Regis_messagee = 'This ID is already used by other user, please try another ID number.'
                        else:
                                Sql = "Insert Into User Values ('{0}', '{1}')".format(UserID, UserPW)
                                cur.execute(Sql)
                                conn.commit()
                                Sql = "Insert Into UserSum Values ('{0}', '')".format(UserID)
                                cur.execute(Sql)
                                conn.commit()
                                Regis_message = 'Registration success'
                        return jsonify(Regis_message)

        if request.method == 'GET':
                if Regis_message != '':
                        return jsonify(Regis_message)
                else:
                        return jsonify('please enter the user ID and password:')

@app.route('/Logout', methods={'GET', 'POST'})
def Logout():
        global UserID, userinput, Error_Code, ShowLog, Regis_message
        if request.method == 'POST':
                if UserID != '':
                        UserID = ''
                        userinput = ''
                        ShowLog = ''
                        Regis_message = ''
                        Error_Code = False
                        Response = 'Logout success'
                return jsonify({'response': Response})

@app.route('/Logout/html', methods={'GET', 'POST'})
def Lo_html():
        global UserID, userinput, Error_Code, ShowLog, Regis_message
        if request.method == 'POST':
                if UserID != '':
                        UserID = ''
                        userinput = ''
                        ShowLog = ''
                        Regis_message = ''
                        Error_Code = False
        return ''

@app.route('/Chatbot', methods={'GET', 'POST'})
def Chat():
        global userinput, response, UserID, ChatLog, Usersum
        if request.method == 'POST':
                if UserID != '':
                        userinput = request.args.get('input')
                        if userinput == 'quit':
                                TotalCount = L_Count(ChatLog)
                                UserSum = str(Chat_ending_summary(ChatLog))
                                Sql = "Select MAX(ChatID) From ChatLog Where UserID = '{0}'".format(UserID)
                                cur.execute(Sql)
                                myresult = cur.fetchone()

                                if myresult and myresult is not None:
                                        NewLogID = str(UserID) + str(int(str(myresult[0]).replace(str(UserID), '', 1)) + 1)
                                else:
                                        NewLogID = str(UserID) + '1'
                                Sql = "Insert Into ChatLog Values (?, ?, ?)"
                                cur.execute(Sql, (NewLogID, UserID, ChatLog))
                                conn.commit()

                                Sql = "Update UserSum Set Sum = ? Where UserID = ? "
                                cur.execute(Sql, (UserSum, UserID))
                                conn.commit()

                                T_List = TotalCount.split(',')
                                for i in range(0, len(T_List)):
                                        Sql = "Select Count From L_Count Where L_Type = '{0}'".format(T_List[i])
                                        cur.execute(Sql)
                                        myresult = cur.fetchone()
                                        if myresult:
                                                Sql = "Update L_Count Set Count = Count + 1 Where L_Type = '{0}'".format(T_List[i])
                                                cur.execute(Sql)
                                                conn.commit()
                                        else:
                                                Sql = "Insert Into L_Count Values ('{0}', 1)".format(T_List[i])
                                                cur.execute(Sql)
                                                conn.commit()

                                return jsonify({'response': 'record clear'})
                        else:
                                userinput = userinput.replace("+", " ")
                                ChatLog += 'User:' + userinput
                                response = str(Chat_process(userinput))
                                ChatLog += 'Bill:' + response.replace('\n', ' ')
                                return jsonify({'response': ChatLog})
                else:
                        userinput = request.args.get('input')
                        response = 'Please login to access the service.'
                        return jsonify({'response': response})

        return ''

@app.route('/L_Count', methods={'GET', 'POST'})
def Count():

        if request.method == 'POST':
                Sql = "Select * From L_Count Order By Count DESC Limit 5"
                cur.execute(Sql)
                myresult = cur.fetchall()
                L_list = []
                for i in range(0, 5):
                        try:
                                L_list.append(str(myresult[i]))
                        except IndexError:
                                continue
                return jsonify(L_list)

@app.route('/Sum', methods={'GET', 'POST'})
def Sum():

        if request.method == 'POST':
                UserID = request.args.get('ID')
                Sql = "Select Sum From UserSum Where UserID = '{0}'".format(UserID)
                cur.execute (Sql)
                myresult = cur.fetchone()
                return jsonify(myresult[0])

def Chat_process(prompt):
        global ChatLog
        completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
                {"role": "system", "content": "Your name is Bill, is a bartender in Hong Kong, skilled in making different cocktails, being creative with different"},
                {"role": "user", "content": prompt}
        ]
        )

        return completion.choices[0].message.content



def Chat_ending_summary(ChatLog):
        completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
                {"role": "system", "content": "Now the whole chat has ended, here is the log for this chat; please try to summarize this user's preferences, includ"},
                {"role": "user", "content": ChatLog}
        ]
        )

        return completion.choices[0].message.content

def L_Count(ChatLog):
        completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
                {"role": "system", "content": "Please show what Types of liquors were mentioned in the chatting log, output a list under the format of separate eac>
                {"role": "user", "content": ChatLog}
        ]
        )

        return completion.choices[0].message.content


@app.route('/Chatlog', methods={'GET', 'POST'})
def Chatlog():
        global UserID, ShowLog
        if request.method == 'GET':
                if UserID != '':
                        Sql = "Select MAX(ChatID) From ChatLog Where UserID = '{0}'".format(UserID)
                        cur.execute(Sql)
                        myresult = cur.fetchone()
                        if myresult[0] != None:
                                Log_Count = str(myresult[0]).replace(UserID, '', 1)
                                Newest_LogID = myresult[0]
                                Sql = "Select Log From ChatLog Where ChatId = '{0}'".format(Newest_LogID)
                                cur.execute(Sql)
                                myresult = cur.fetchone()
                                Log = myresult[0]
                                return jsonify(str(Log))
                        else:
                                return jsonify('There are no record of chatting with Bill! He will be happy to meet a new user in Chat & Shake page!')
                else:
                        return jsonify('Please login to access the service.')

        if request.method == 'POST':
                if UserID != '':
                        if request.args.get('LogID') != '':
                                Log_ID = str(UserID) + str(request.args.get('LogID'))
                                Sql = "Select Log From ChatLog Where ChatID = '{0}'".format(Log_ID)
                                cur.execute(Sql)
                                myresult = cur.fetchone()
                                if myresult is not None:
                                        Log = myresult[0]
                                        ShowLog = str(Log)
                                        return jsonify(ShowLog)
                                else:
                                        return jsonify('Worng log ID! PLease check the entered ID.')
                        elif ShowLog != '':
                                return jsonify(ShowLog)
                        else:
                                Sql = "Select MAX(ChatID)From ChatLog Where UserID = '{0}'".format(UserID)
                                cur.execute(Sql)
                                myresult = cur.fetchone()
                                if myresult[0] != None:
                                        Log_Count = str(myresult[0]).replace (UserID, '', 1)
                                        ShowLog = ''
                                        return jsonify('There are total of '+ str(Log_Count) + 'record/s.')
                                else:
                                        return jsonify('There are no record of chatting with Bill! He will be happy to meet a new user in Chat & Shake page!')
                else:
                        return jsonify('Please login to accsee the service.')

@app.route('/Response', methods={'GET'})
def Response():

        if request.method == 'GET':
                Response = userinput
                return jsonify({'response': Response})

@app.route('/Response/html', methods={'GET'})
def R_html():

        global response, userinput
        if request.method == 'GET':
                if userinput != '':
                        if userinput == 'quit':
                                Response = 'Bill: Thank you for using our services, all the chatting record will saved in My Cocktails page, hope to see you soon!'
                        else:
                                Response = 'Bill:' + response.replace('\n', ' ')
                else:
                        Response = 'Bill: HI! Wellcome to the first virtual-bar in Hong Kong, I am your bartender tonight, how can I help you?'
                return jsonify (Response)

if __name__ == '__main__':
        app.run(host="0.0.0.0", port=8080, debug=True)

