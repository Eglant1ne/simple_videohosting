package service

import (
	"fmt"
	"log"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	amqp "github.com/rabbitmq/amqp091-go"
)

type RabbitMQService struct {
	Conn    *amqp.Connection
	Channel *amqp.Channel
	Config  *config.Config
}

func NewRabbitMQService(cfg *config.Config) *RabbitMQService {
	conn, err := amqp.Dial(fmt.Sprintf("amqp://%s:%s@rabbitmq:5672/", cfg.RabbitmqUser, cfg.RabbitmqPass))
	if err != nil {
		log.Panicf("Failed to connect to RabbitMQ: %v", err)
	}

	channel, err := conn.Channel()
	if err != nil {
		log.Panicf("Failed to open channel: %v", err)
	}

	_, err = channel.QueueDeclare(
		"unprocessed_video_uploaded",
		true,
		false,
		false,
		false,
		amqp.Table{"delivery_mode": 2},
	)
	if err != nil {
		log.Panicf("Failed to declare queue: %v", err)
	}

	return &RabbitMQService{
		Conn:    conn,
		Channel: channel,
		Config:  cfg,
	}
}

func (r *RabbitMQService) PublishVideoUploadEvent(videoPath string, user_id int) error {
	return r.Channel.Publish(
		"",
		"unprocessed_video_uploaded",
		false,
		false,
		amqp.Publishing{
			ContentType:  "application/json",
			DeliveryMode: amqp.Persistent,
			Body:         []byte(fmt.Sprintf(`{"video_path": "%s", "user_id": "%d"}`, videoPath, user_id)),
		},
	)
}

func (r *RabbitMQService) Close() {
	if err := r.Channel.Close(); err != nil {
		log.Printf("Failed to close RabbitMQ channel: %v", err)
	}
	if err := r.Conn.Close(); err != nil {
		log.Printf("Failed to close RabbitMQ connection: %v", err)
	}
}
