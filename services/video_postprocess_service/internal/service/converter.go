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

func (vp *VideoProcessor) StartWorkers() {
	for i := 0; i < vp.cfg.ConsumeWorkers; i++ {
		vp.wg.Add(1)
		go vp.worker(i)
	}
}

func (vp *VideoProcessor) worker(workerID int) {
	defer vp.wg.Done()

	ch, err := vp.rabbitConn.Channel()
	if err != nil {
		log.Printf("Worker %d: failed to open channel: %v", workerID, err)
		return
	}
	defer ch.Close()

	msgs, err := ch.Consume(
		"convert_video_to_hls",
		fmt.Sprintf("worker_%d", workerID),
		false,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Printf("Worker %d: failed to register consumer: %v", workerID, err)
		return
	}

	for msg := range msgs {
		if err := vp.processVideo(msg); err != nil {
			log.Printf("Worker %d: failed to process video: %v", workerID, err)
			msg.Nack(false, true)
			continue
		}
		msg.Ack(false)
	}
}

func (vp *VideoProcessor) processVideo(msg amqp.Delivery) error {
	var task struct {
		VideoPath string `json:"video_path"`
		UUID      string `json:"uuid"`
	}

	if err := json.Unmarshal(msg.Body, &task); err != nil {
		return fmt.Errorf("failed to parse message: %v", err)
	}

	tempDir, err := os.MkdirTemp("", "video_processing")
	if err != nil {
		return fmt.Errorf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	inputFile := filepath.Join(tempDir, "input.mp4")
	err = vp.minio.Client.FGetObject(context.Background(), vp.cfg.Bucket, task.VideoPath, inputFile, minio.GetObjectOptions{})
	if err != nil {
		return fmt.Errorf("failed to download video from MinIO: %v", err)
	}

	resolutions := []string{
		"3840:2160", // 4K
		"2560:1440", // 2K
		"1920:1080", // 1080p
		"1280:720",  // 720p
		"854:480",   // 480p
		"640:360",   // 360p
		"426:240",   // 240p
		"256:144",   // 144p
	}

	for _, res := range resolutions {
		if err := vp.convertToHLS(inputFile, task.UUID, res, tempDir); err != nil {
			return fmt.Errorf("failed to convert to %s: %v", res, err)
		}
	}

	if err := vp.sendConfirmation(task.UUID); err != nil {
		return fmt.Errorf("failed to send confirmation: %v", err)
	}

	return nil
}

func (vp *VideoProcessor) convertToHLS(inputFile, videoUUID, resolution, tempDir string) error {
	resParts := strings.Split(resolution, ":")
	resName := resParts[1] + "p"
	outputDir := filepath.Join(tempDir, resName)

	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output dir: %v", err)
	}

	outputPrefix := fmt.Sprintf("%s-%s", resName, videoUUID)
	cmd := exec.Command("ffmpeg",
		"-i", inputFile,
		"-vf", fmt.Sprintf("scale=%s", resolution),
		"-c:v", "libx264",
		"-preset", "fast",
		"-profile:v", "baseline",
		"-level", "3.0",
		"-start_number", "0",
		"-hls_time", "5",
		"-hls_list_size", "0",
		"-f", "hls",
		filepath.Join(outputDir, fmt.Sprintf("%s.m3u8", outputPrefix)),
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

		_, err = vp.minio.Client.FPutObject(context.Background(),
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
	defer ch.Close()

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
