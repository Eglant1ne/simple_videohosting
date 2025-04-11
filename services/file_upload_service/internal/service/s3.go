package service

import (
	"bytes"
	"context"
	"io"
	"log"
	"time"

	appcfg "github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

type MinIOService struct {
	Client *minio.Client
	Config appcfg.Config
}

func NewMinIOService(cfg appcfg.Config) *MinIOService {
	client, err := minio.New(cfg.Endpoint, &minio.Options{
		Creds:  credentials.NewStaticV4(cfg.AccessKey, cfg.SecretKey, ""),
		Secure: false,
		Region: cfg.Region,
	})
	if err != nil {
		log.Fatalf("failed to initialize MinIO client: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	exists, err := client.BucketExists(ctx, cfg.Bucket)
	if err != nil {
		log.Fatalf("failed to check bucket existence: %v", err)
	}

	if !exists {
		err = client.MakeBucket(ctx, cfg.Bucket, minio.MakeBucketOptions{Region: cfg.Region})
		if err != nil {
			log.Fatalf("failed to create bucket: %v", err)
		}
	}

	return &MinIOService{
		Client: client,
		Config: cfg,
	}
}

func (s *MinIOService) UploadStream(ctx context.Context, key string, body io.Reader, size int64) error {
	_, err := s.Client.PutObject(ctx, s.Config.Bucket, key, body, size, minio.PutObjectOptions{
		ContentType: "application/octet-stream",
	})
	return err
}

func (s *MinIOService) UploadChunk(ctx context.Context, key string, chunk []byte) error {
	return s.UploadStream(ctx, key, bytes.NewReader(chunk), int64(len(chunk)))
}
