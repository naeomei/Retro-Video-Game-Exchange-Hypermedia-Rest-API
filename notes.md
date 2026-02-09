kafka notes: 
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
