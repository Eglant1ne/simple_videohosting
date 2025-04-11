package service

import (
	"bytes"
	"context"
	"io"
	"log"

	appcfg "github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

type S3Service struct {
	Client *s3.Client
	Config appcfg.Config
}

func NewS3Service(cfg appcfg.Config) *S3Service {
	awsCfg, err := config.LoadDefaultConfig(context.TODO(),
		config.WithRegion(cfg.Region),
		config.WithCredentialsProvider(credentials.NewStaticCredentialsProvider(cfg.AccessKey, cfg.SecretKey, "")),
	)
	if err != nil {
		log.Fatalf("failed to load AWS config: %v", err)
	}

	client := s3.NewFromConfig(awsCfg, func(o *s3.Options) {
		o.UsePathStyle = cfg.UsePathStyle
		o.EndpointResolver = s3.EndpointResolverFromURL(cfg.Endpoint)
	})

	return &S3Service{Client: client, Config: cfg}
}

func (s *S3Service) UploadStream(ctx context.Context, key string, body io.Reader) error {
	_, err := s.Client.PutObject(ctx, &s3.PutObjectInput{
		Bucket: aws.String(s.Config.Bucket),
		Key:    aws.String(key),
		Body:   body,
	})
	return err
}

func (s *S3Service) UploadChunk(ctx context.Context, key string, chunk []byte) error {
	return s.UploadStream(ctx, key, bytes.NewReader(chunk))
}
