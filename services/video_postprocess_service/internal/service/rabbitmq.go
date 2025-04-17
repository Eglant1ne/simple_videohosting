package service

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"path/filepath"
	"strings"

	amqp "github.com/rabbitmq/amqp091-go"
)

func (vp *VideoProcessor) StartConsumers() {
	ch, err := vp.rabbitConn.Channel()
	if err != nil {
		log.Fatalf("Failed to open channel: %v", err)
	}
	defer ch.Close()

	err = ch.ExchangeDeclare(
		"unprocessed_video_uploaded",
		"topic",
		true,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Fatalf("Failed to declare exchange: %v", err)
	}

	q, err := ch.QueueDeclare(
		"convert_video_to_hls",
		true,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Fatalf("Failed to declare queue: %v", err)
	}

	err = ch.QueueBind(
		q.Name,
		"#",
		"unprocessed_video_uploaded",
		false,
		nil,
	)
	if err != nil {
		log.Fatalf("Failed to bind queue: %v", err)
	}

	msgs, err := ch.Consume(
		q.Name,
		"video_processor",
		false,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Fatalf("Failed to register consumer: %v", err)
	}

	for msg := range msgs {
		var uploadEvent struct {
			UserID    string `json:"user_id"`
			VideoPath string `json:"video_path"`
		}

		if err := json.Unmarshal(msg.Body, &uploadEvent); err != nil {
			log.Printf("Failed to parse message: %v", err)
			_ = msg.Nack(false, false)
			continue
		}

		videoUUID := strings.TrimSuffix(filepath.Base(uploadEvent.VideoPath), filepath.Ext(uploadEvent.VideoPath))

		if err := vp.publishConversionTask(uploadEvent.VideoPath, videoUUID); err != nil {
			log.Printf("Failed to publish conversion task: %v", err)
			_ = msg.Nack(false, true)
			continue
		}

		_ = msg.Ack(false)
	}
}

func (vp *VideoProcessor) publishConversionTask(videoPath, videoUUID string) error {
	ch, err := vp.rabbitConn.Channel()
	if err != nil {
		return err
	}
	defer ch.Close()

	return ch.PublishWithContext(context.Background(),
		"",
		"convert_video_to_hls",
		false,
		false,
		amqp.Publishing{
			ContentType:  "application/json",
			DeliveryMode: amqp.Persistent,
			MessageId:    videoUUID,
			Body:         fmt.Appendf(nil, `{"video_path": "%s", "uuid": "%s"}`, videoPath, videoUUID),
		})
}
