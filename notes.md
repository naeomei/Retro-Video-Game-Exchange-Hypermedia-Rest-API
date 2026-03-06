random notes:
synchronous: in order one after another 



kafka notes: 
 what even is kafka: a message broker (like a message bus or queue system
what is does:
- recieves messages from produces (my api)
-stores them in "topics" (like categories)
- delivers them to consumers (email services)

helpful anology : think of it like a post office
- api drops letters in the mailbox
-letters wait in the postbox
- mail carrier picks them up later 

)
producer 
what is a producer? its like a program that sends messages to kafka. like a sender who drops letters in a mailbox
when producer command:
docker exec -it kafka-kraft /opt/kafka/bin/kafka-console-producer.sh \
  --topic trade-offers \
  --bootstrap-server localhost:9092

you're: opening a connection to kafka and telling kafka " i iwant to send messages to the trade-offers topic" and waiting for you to type messages 
producer is the thing that sends messages 
starting the producer is like opening a program that lets you type messages into kafka 

after you start the producer feed it : {"event": "created", "offer_id": 1, "game": "Super Mario Bros", "from": "alice", "to": "bob"}
{"event": "created", "offer_id": 2, "game": "Legend of Zelda", "from": "charlie", "to": "diana"}
{"event": "accepted", "offer_id": 1, "accepted_by": "bob"}

mmm then in a new window :
 docker exec -it kafka-kraft /opt/kafka/bin/kafka-console-consumer.sh --topic trade-offers --bootstrap-server localhost:9092 --from-beginning

lab 3 notes : 
asynchronous event processing - 

problem right now without kafka fr,  if you try to send out emails straight up in the code it'll be really slow, api response time goes from 10ms to 5s, if the email server is down, the api fails, can't scale the email sending independently, overall bad user experience 

solution: asynchronous messaging 
new architecture for lab 3 old way vs new way:
old:
user then api then db then send email (1) then send email (2) then response 
new:
user then api then db then kafka then reponse then waiting in queue then email service then email (1) then email (2) (happens later the user doesnt wait)
why chose new 
: fast response, scalable, if email service crashes messages wait in kafka safley, independent can update email service without touching api, 

another analogy:
api = waiter (takes orders quickly doesnt cook)
kafka = order ticket rail (holds tickes until chef is ready)
email service = chef cooks food slowly one order at a time 
email = the meal being served 
the waiter doesnt stand in the kitchen waiting for the food to cook they drop the ticket and go serve more customers the chef picks up tickets when theyre ready and cooks at their own pace