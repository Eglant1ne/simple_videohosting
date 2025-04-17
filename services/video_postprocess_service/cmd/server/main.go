package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/handler"
	"github.com/go-chi/chi/v5"
	amqp "github.com/rabbitmq/amqp091-go"
)

type VideoEvent struct {
	VideoPath string `json:"video_path"`
	UUID      string `json:"uuid"`
}

func main() {
	cfg := config.Load()
	broker_conn, err := amqp.Dial(fmt.Sprintf("amqp://%s:%s@rabbitmq:5672/", cfg.RabbitmqUser, cfg.RabbitmqPass))
	if err != nil {
		log.Panicf("%s", err)
	}

	convert_to_hls_queue_name := "convert_video_to_hls"
	conifrm_video_hls_convert_name := "confirm_video_hls_converting"

	rabbitmq_channel, err := broker_conn.Channel()

	rabbitmq_channel.QueueDeclare(
		convert_to_hls_queue_name,
		true,
		false,
		false,
		false,
		amqp.Table{"delivery_mode": 2},
	)

	rabbitmq_channel.QueueDeclare(
		conifrm_video_hls_convert_name,
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

	log.Println("Server listening on :8090")

	if err := http.ListenAndServe(":8090", r); err != nil {
		log.Fatalf("server error: %v", err)
	}

}
