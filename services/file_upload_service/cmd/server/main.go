package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/handler"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	"github.com/go-chi/chi/v5"
)

func main() {
	cfg := config.Load()

	minioSvc := service.NewMinIOService(cfg)
	rabbitSvc := service.NewRabbitMQService(&cfg)
	defer rabbitSvc.Close()

	r := chi.NewRouter()
	r.Get("/health", handler.HealthCheckHandler)
	r.Post("/upload/video", handler.UploadHandler(minioSvc, &cfg, rabbitSvc))
	server := &http.Server{
		Addr:    ":8080",
		Handler: r,
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	go func() {
		log.Println("Server listening on :8080")
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server error: %v", err)
		}
	}()
	<-ctx.Done()

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Fatalf("Server Shutdown Failed: %+v", err)
	}

	log.Println("Server exited properly")
}
