package service

import (
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
		log.Fatalf("%v", cfg.Endpoint)
		log.Fatalf("failed to initialize MinIO client: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	exists, err := client.BucketExists(ctx, cfg.Bucket)
	if err != nil {
		log.Fatalf("failed to check bucket existence: %v", err)
	}

	if !exists {
		err = client.MakeBucket(ctx, cfg.Bucket, minio.MakeBucketOptions{})
		if err != nil {
			log.Fatalf("failed to create bucket: %v", err)
		}
	}

	return &MinIOService{
		Client: client,
		Config: cfg,
	}
}

func (s *MinIOService) UploadPart(ctx context.Context, objectName, uploadID string, partNumber int, reader io.Reader, partSize int64) error {
	s.Client.PutObjectPart(ctx, s.Config.Bucket, objectName, uploadID, partNumber, reader, partSize, "", "", nil)
}

func (s *MinIOService) CompleteUpload(ctx context.Context, objectName, uploadID string, parts []minio.CompletePart) (*minio.UploadInfo, error) {
	return s.Client.CompleteMultipartUpload(ctx, s.Config.Bucket, objectName, uploadID, minio.CompleteMultipartUpload{
		Parts: parts,
	})
}

func (s *MinIOService) AbortUpload(ctx context.Context, objectName, uploadID string) error {
	return s.Client.AbortMultipartUpload(ctx, s.Config.Bucket, objectName, uploadID)
}
