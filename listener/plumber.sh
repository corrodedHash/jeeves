plumber write rabbit --address="amqp://rabbitmq" --routing-key=webhooks --input="{ \"project\" = \"$1\"}" --exchange-name="jeeves"
