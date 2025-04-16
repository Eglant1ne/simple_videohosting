package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/handler"
	"github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/service"
	"github.com/go-chi/chi/v5"
)

type VideoEvent struct {
	VideoPath string `json:"video_path"`
	UUID      string `json:"uuid"`
}

func main() {
	cfg := config.Load()
	kafkaConfig := service.KafkaConsumerConfig()
	//minioSvc := service.NewMinIOService(cfg)

	producer, err := service.NewKafkaProducer([]string{"kafka:9092"})
	if err != nil {
		fmt.Println("Error loading kafka")
	}
	log.Println("Kafka is loaded ")
	//kafkaTopic := "confirm_video_hls_converting"
	defer producer.Close()

	consumer, err := service.NewKafkaConsumer(
		cfg.KafkaBrokers,
		"convert_video_to_hls",
		kafkaConfig,
		cfg.ConsumeWorkers,
	)
	if err != nil {
		log.Fatalf("Error initialization Consumer: %v", err)
	}
	defer consumer.Close()

	r := chi.NewRouter()
	//healthcheck
	r.Get("/health", handler.HealthCheckHandler)

	log.Println("Server listening on :8090")

	if err := http.ListenAndServe(":8090", r); err != nil {
		log.Fatalf("server error: %v", err)
	}

}
