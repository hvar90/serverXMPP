#!/usr/bin/env python
import sys, json, xmpp, random, string,os
from common              import payload, RpcClient
import logging
import logging.config



root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)
 
SERVER = 'gcm.googleapis.com'
PORT = 5235
USERNAME = "11178319894"
PASSWORD = "AIzaSyAAFlAM3nJkwF_Lycelx5J5RC0aHfyHPT4"
REGISTRATION_ID = "APA91bGvS3YrGOtecgmFUqTz84iEMsdw4MUNAKNth_8najuIuRTbZ248YZd1CZxLlTohowUziQiod4Rv6Ej6jzS9Z_WmF3JfTY5hch33H2I1WFn8QjgdgyX9IZPUwjU5o7aaOtFEX9aEJeSQSLaXy5vOWbN2P-XGRoPBiFWuDjWulj3eiY8nXr4"



unacked_messages_quota = 100
send_queue = []

# Return a random alphanumerical id
def random_id():
  rid = ''
  for x in range(8): rid += random.choice(string.ascii_letters + string.digits)
  return rid

def message_callback(session, message):
  global unacked_messages_quota
  gcm = message.getTags('gcm')
  if gcm:
    gcm_json = gcm[0].getData()
    msg = json.loads(gcm_json)
    if not msg.has_key('message_type'):
      # Acknowledge the incoming message immediately.
      send({'to': msg['from'],
            'message_type': 'ack',
            'message_id': msg['message_id']})
      # Queue a response back to the server.
      if msg.has_key('from'):
        # Send a dummy echo response back to the app that sent the upstream message.
       
        print " [x] Requesting cel" + msg['from']
        msg['data']['idCel'] = msg['from']
        payloadObj= payload("command", msg['data']['command'] , msg['data'])
        response = rpc.call(payloadObj)
        print " [.] Got %r" % (response,)
        if  response['type'] == 'response'  :
            send_queue.append({'to': msg['from'],
                               'message_id': random_id(),
                               'data': {'response': response['response'],'type': 'response'}})  
        else:
            send_queue.append({'to': msg['from'],                                                           
                               'message_id': random_id(),
                               'data': {'error': response['error'],'type': 'error'}})                    
                    
    elif msg['message_type'] == 'ack' or msg['message_type'] == 'nack':
      unacked_messages_quota += 1

def send(json_dict):
  template = ("<message><gcm xmlns='google:mobile:data'>{1}</gcm></message>")
  client.send(xmpp.protocol.Message(
      node=template.format(client.Bind.bound[0], json.dumps(json_dict))))

def flush_queued_messages():
  global unacked_messages_quota
  while len(send_queue) and unacked_messages_quota > 0:
    send(send_queue.pop(0))
    unacked_messages_quota -= 1

client = xmpp.Client('gcm.googleapis.com', debug=['socket'],
                    port=int(os.environ.get("PORT")))
                    
client.connect(server=(SERVER,PORT), secure=1, use_srv=False)
auth = client.auth(USERNAME, PASSWORD)
if not auth:
  print 'Authentication failed!'
  sys.exit(1)

client.RegisterHandler('message', message_callback)

#send_queue.append({'to': REGISTRATION_ID,
                   #'message_id': 'reg_id',
                   #'data': {'message_destination': 'RegId',
                            #'message_id': random_id()}})

while True: 
  rpc = RpcClient()
  client.Process(1)
  flush_queued_messages()
