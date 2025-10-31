package service

import (
	"log"

	amqp "github.com/rabbitmq/amqp091-go"
)

func (vp *VideoProcessor) StartConsumers() error {
	ch, err := vp.rabbitConn.Channel()
	if err != nil {
		log.Fatalf("Failed to open channel: %v", err)
		return err
	}

	_, err = ch.QueueDeclare(
		"unprocessed_video_uploaded",
		true,
		false,
		false,
		false,
		amqp.Table{"delivery_mode": 2},
	)

	q, err := ch.QueueDeclare(
		"convert_video_to_hls",
		true,
		false,
		false,
		false,
		amqp.Table{"delivery_mode": 2},
	)

	if err != nil {
		log.Fatalf("Failed to declare queue: %v", err)
		return err
	}

	err = ch.Qos(vp.cfg.ConsumeWorkers, 0, false)
	if err != nil {
		log.Fatalf("Ошибка установки QoS: %s", err)
	}

	msgs, err := ch.Consume(
		q.Name,
		"",
		false,
		false,
		false,
		false,
		nil,
	)

	if err != nil {
		log.Fatalf("Failed to register consumer: %v", err)
		return err
	}

	go func() {
		for msg := range msgs {
			go func(m amqp.Delivery) {
				log.Printf("Rabbitmq Text: %s", msg.Body)
				err := vp.processVideo(m)

				if err != nil {
					log.Printf("Ошибка при обработке сообщения: %s", err)
					if err := m.Nack(false, true); err != nil {
						log.Printf("Ошибка при отклонении сообщения: %s", err)
					}
					return
				}

				if err := m.Ack(false); err != nil {
					log.Printf("Ошибка подтверждения сообщения: %s", err)
				}
			}(msg)
		}
		defer vp.rabbitConn.Close()
		defer ch.Close()
	}()
	log.Println("Начало обработки сообщений.")
	return nil
}
