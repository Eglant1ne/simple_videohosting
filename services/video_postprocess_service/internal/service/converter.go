package service

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	appcfg "github.com/Eglant1ne/simple_videohosting/services/video_postprocess_service/internal/config"
	"github.com/minio/minio-go/v7"
	amqp "github.com/rabbitmq/amqp091-go"
)

type VideoProcessor struct {
	cfg        *appcfg.Config
	minio      *MinIOService
	rabbitConn *amqp.Connection
	wg         sync.WaitGroup
}

func NewVideoProcessor(cfg *appcfg.Config) (*VideoProcessor, error) {
	minioService := NewMinIOService(*cfg)

	rabbitConn, err := amqp.Dial(fmt.Sprintf("amqp://%s:%s@rabbitmq:5672/", cfg.RabbitmqUser, cfg.RabbitmqPass))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to RabbitMQ: %v", err)
	}

	return &VideoProcessor{
		cfg:        cfg,
		minio:      minioService,
		rabbitConn: rabbitConn,
	}, nil
}

func (vp *VideoProcessor) processVideo(msg amqp.Delivery) error {
	log.Printf("Началась обработка видео")
	var task struct {
		VideoPath string `json:"video_path"`
		UUID      string `json:"uuid"`
	}

	if err := json.Unmarshal(msg.Body, &task); err != nil {
		return fmt.Errorf("failed to parse message: %v", err)
	}

	tempDir, err := os.MkdirTemp("", task.UUID)
	if err != nil {
		return fmt.Errorf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	inputFile := filepath.Join(tempDir, task.VideoPath)
	ctx, cancel := context.WithTimeout(context.Background(), vp.cfg.MinioTimeout*time.Second)
	defer cancel()
	err = vp.minio.Client.FGetObject(ctx, vp.cfg.Bucket, task.VideoPath, inputFile, minio.GetObjectOptions{})
	if err != nil {
		return fmt.Errorf("failed to download video from MinIO: %v", err)
	}

	video_width, video_height, err := getVideoResolution(inputFile)
	if err != nil {
		return fmt.Errorf("failed to get video resolution: %v", err)
	}

	video_resolutions := []string{"256:144"} //140p

	resolutions := [][]int{
		{3840, 2160}, //4k
		{2560, 1440}, //2k
		{1920, 1080}, //1080p
		{1280, 720},  //720p
		{854, 480},   //480p
		{640, 360},   //360p
		{426, 240},   //240p
	}

	var builder strings.Builder
	builder.WriteString(fmt.Sprint("ffmpeg -i %s -master_pl_name master.m3u8 ", inputFile))

	for _, resolution := range resolutions {
		if resolution[0] <= video_width && resolution[1] <= video_height {
			resolution_str := fmt.Sprintf("%d:%d", resolution[0], resolution[1])
			video_resolutions = append(video_resolutions, resolution_str)
			builder.WriteString(fmt.Sprintf("-vf \"scale=%s\" -c:v libx264 -preset fast -profile:v baseline -level 3.0 -loglevel warning -start_number 0 -hls_time 5 -hls_list_size 0 - f hls \\\n", resolution_str))
		}
	}

	for _, converted_resolution := range video_resolutions {
		if err := vp.convertToHLS(inputFile, task.UUID, converted_resolution, tempDir); err != nil {
			return fmt.Errorf("failed to convert to %s: %v", converted_resolution, err)
		}
	}

	builder.WriteString(filepath.Join(filepath.Join(tempDir, "hls"), fmt.Sprintf("%s.m3u8", "master")))
	master_file_command := builder.String()
	exec.Command(master_file_command)

	if err := vp.minio.Client.RemoveObject(context.Background(), vp.cfg.Bucket, task.VideoPath, minio.RemoveObjectOptions{}); err != nil {
		return fmt.Errorf("failed to remove video from MinIO: %v", err)
	}

	if err := vp.sendConfirmation(task.UUID); err != nil {
		return fmt.Errorf("failed to send confirmation: %v", err)
	}

	return nil
}

func (vp *VideoProcessor) convertToHLS(inputFile, videoUUID, resolution, tempDir string) error {
	resParts := strings.Split(resolution, ":")

	resName := fmt.Sprintf("%sp-%s", resParts[1], videoUUID)
	outputDir := filepath.Join(tempDir, "hls")

	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output dir: %v", err)
	}

	cmd := exec.Command("ffmpeg",
		"-i", inputFile,
		"-vf", fmt.Sprintf("scale=%s", resolution),
		"-c:v", "libx264",
		"-preset", "fast",
		"-profile:v", "baseline",
		"-level", "3.0",
		"-loglevel", "warning",
		"-start_number", "0",
		"-hls_time", "5",
		"-hls_list_size", "0",
		"-f", "hls",
		filepath.Join(outputDir, fmt.Sprintf("%s.m3u8", resName)),
	)

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("ffmpeg command failed: %v", err)
	}

	files, err := os.ReadDir(outputDir)
	if err != nil {
		return fmt.Errorf("failed to read output dir: %v", err)
	}

	for _, file := range files {
		if file.IsDir() {
			continue
		}

		localPath := filepath.Join(outputDir, file.Name())
		objectPath := fmt.Sprintf("%s/%s/%s", vp.minio.VideoFilesFolder, videoUUID, file.Name())

		ctx, cancel := context.WithTimeout(context.Background(), vp.cfg.MinioTimeout*time.Second)
		defer cancel()
		_, err = vp.minio.Client.FPutObject(ctx,
			vp.cfg.Bucket,
			objectPath,
			localPath,
			minio.PutObjectOptions{
				ContentType: getContentType(file.Name()),
			})
		if err != nil {
			return fmt.Errorf("failed to upload %s: %v", file.Name(), err)
		}
	}

	return nil
}

func (vp *VideoProcessor) sendConfirmation(videoUUID string) error {
	ch, err := vp.rabbitConn.Channel()
	if err != nil {
		return err
	}

	return ch.PublishWithContext(context.Background(),
		"",
		"confirm_video_hls_converting",
		false,
		false,
		amqp.Publishing{
			ContentType:  "application/json",
			DeliveryMode: amqp.Persistent,
			MessageId:    videoUUID,
			Body:         []byte(fmt.Sprintf(`{"uuid": "%s"}`, videoUUID)),
		})
}

func getContentType(filename string) string {
	switch filepath.Ext(filename) {
	case ".m3u8":
		return "application/vnd.apple.mpegurl"
	case ".ts":
		return "video/MP2T"
	default:
		return "application/octet-stream"
	}
}

func (vp *VideoProcessor) Close() {
	vp.wg.Wait()
	vp.rabbitConn.Close()
}
