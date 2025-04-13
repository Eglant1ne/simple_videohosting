package main

import (
	"log"
	"net/http"
	"os"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/handler"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	"github.com/go-chi/chi"
)

const (
	tmpDir       = "../.././tmp"
	chunksDir    = "../.././tmp/chunks"
	chunkPattern = "chunk_%03d.mp4"

	chunkDuration = 5
	maxUploadSize = 20 << 30
)

func main() {
	if err := os.MkdirAll(tmpDir, 0755); err != nil {
		log.Fatalln("Ошибка создания tmpDir:", err)
	}
	if err := os.MkdirAll(chunksDir, 0755); err != nil {
		log.Fatalln("Ошибка создания chunksDir:", err)
	}

	cfg := config.Load()

	minioSvc := service.NewMinIOService(cfg)

	r := chi.NewRouter()
	//healthcheck
	r.Get("/health", handler.HealthCheckHandler)

	r.Post("/upload", handler.uploadHandler(minioSvc, cfg))

	log.Println("Server listening on :8080")
	if err := http.ListenAndServe(":8080", r); err != nil {
		log.Fatalf("server error: %v", err)
	}
}
