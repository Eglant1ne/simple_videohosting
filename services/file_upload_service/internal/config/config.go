package config

import (
	"log"
	"os"
	"strconv"
	"strings"
	"time"
)

type Config struct {
	RabbitmqUser string
	RabbitmqPass string
	DebugMode    bool
	Bucket       string
	Region       string
	Endpoint     string
	AccessKey    string
	SecretKey    string
	MinioTimeout time.Duration
}

func Load() Config {
	timeout, err := strconv.Atoi(os.Getenv("MINIO_STALE_UPLOADS_EXPIRY"))
	if err != nil {
		log.Fatal("Не удалось инициализировать minio timeout")
	}
	return Config{
		RabbitmqUser: os.Getenv("RABBITMQ_DEFAULT_USER"),
		RabbitmqPass: os.Getenv("RABBITMQ_DEFAULT_PASS"),
		DebugMode:    strings.ToLower(os.Getenv("DEBUG_MODE")) == "true",
		Bucket:       os.Getenv("S3_BUCKET"),
		Region:       os.Getenv("S3_REGION"),
		Endpoint:     os.Getenv("MINIO_SERVER_URL"),
		AccessKey:    os.Getenv("MINIO_ROOT_USER"),
		SecretKey:    os.Getenv("MINIO_ROOT_PASSWORD"),
		MinioTimeout: time.Duration(timeout),
	}
}
