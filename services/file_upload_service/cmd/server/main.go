package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/handler"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	"github.com/go-chi/chi/v5"
	amqp "github.com/rabbitmq/amqp091-go"
)

func main() {
	cfg := config.Load()

	minioSvc := service.NewMinIOService(cfg)

	broker_conn, err := amqp.Dial(fmt.Sprintf("amqp://%s:%s@rabbitmq:5672/", cfg.RabbitmqUser, cfg.RabbitmqPass))
	if err != nil {
		log.Panicf("Error loading rabbitmq %s", err)
	}

	log.Println("unprocessed_video_uploaded ")
	rabbitmq_queue_name := "unprocessed_video_uploaded"
	rabbitmq_channel, err := broker_conn.Channel()

	rabbitmq_channel.QueueDeclare(
		rabbitmq_queue_name,
		true,
		false,
		false,
		false,
		amqp.Table{"delivery_mode": 2},
	)

	if err != nil {
		log.Panicf("Error loading rabbitmq")
	}
	defer rabbitmq_channel.Close()
	defer broker_conn.Close()

	r := chi.NewRouter()
	//healthcheck
	r.Get("/health", handler.HealthCheckHandler)

	r.Post("/upload/video", handler.UploadHandler(minioSvc, &cfg, rabbitmq_channel, rabbitmq_queue_name))

	log.Println("Server listening on :8080")

	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatalf("server error: %v", err)
	}

}
