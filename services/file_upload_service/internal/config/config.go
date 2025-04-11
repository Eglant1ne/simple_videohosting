package config

import (
	"os"
)

type Config struct {
	Bucket    string
	Region    string
	Endpoint  string
	AccessKey string
	SecretKey string
}

func Load() Config {
	return Config{
		Bucket:    os.Getenv("S3_BUCKET"),
		Region:    os.Getenv("S3_REGION"),
		Endpoint:  os.Getenv("MINIO_SERVER_URL"),
		AccessKey: os.Getenv("MINIO_ROOT_USER"),
		SecretKey: os.Getenv("MINIO_ROOT_PASSWORD"),
	}
}
