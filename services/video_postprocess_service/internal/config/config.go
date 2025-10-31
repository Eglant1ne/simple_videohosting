package config

import (
	"log"
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	DebugMode      bool
	Bucket         string
	Region         string
	Endpoint       string
	AccessKey      string
	SecretKey      string
	ConsumeWorkers int
	RabbitmqUser   string
	RabbitmqPass   string
	MinioTimeout   time.Duration
}

func Load() Config {
	workers, err := strconv.Atoi(os.Getenv("VIDEO_POSTPROCESS_WORKERS"))
	if err != nil || workers <= 0 {
		workers = 5
	}

	timeout, err := strconv.Atoi(os.Getenv("MINIO_STALE_UPLOADS_EXPIRY"))
	if err != nil {
		log.Fatal("Не удалось инициализировать minio timeout")
	}

	return Config{
		DebugMode:      strings.ToLower(os.Getenv("DEBUG_MODE")) == "true",
		Bucket:         os.Getenv("S3_BUCKET"),
		Region:         os.Getenv("S3_REGION"),
		Endpoint:       os.Getenv("MINIO_SERVER_URL"),
		AccessKey:      os.Getenv("MINIO_ROOT_USER"),
		SecretKey:      os.Getenv("MINIO_ROOT_PASSWORD"),
		ConsumeWorkers: workers,
		RabbitmqUser:   os.Getenv("RABBITMQ_DEFAULT_USER"),
		RabbitmqPass:   os.Getenv("RABBITMQ_DEFAULT_PASS"),
		MinioTimeout:   time.Duration(timeout),
	}
}
