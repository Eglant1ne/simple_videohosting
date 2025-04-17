package config

import (
	"os"
	"strings"
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
}

func Load() Config {
	return Config{
		RabbitmqUser: os.Getenv("RABBITMQ_DEFAULT_USER"),
		RabbitmqPass: os.Getenv("RABBITMQ_DEFAULT_PASS"),
		DebugMode:    strings.ToLower(os.Getenv("DEBUG_MODE")) == "true",
		Bucket:       os.Getenv("S3_BUCKET"),
		Region:       os.Getenv("S3_REGION"),
		Endpoint:     os.Getenv("MINIO_SERVER_URL"),
		AccessKey:    os.Getenv("MINIO_ROOT_USER"),
		SecretKey:    os.Getenv("MINIO_ROOT_PASSWORD"),
	}
}
