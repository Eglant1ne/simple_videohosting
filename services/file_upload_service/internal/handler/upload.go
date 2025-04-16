package handler

import (
	"context"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"path/filepath"
	"time"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	"github.com/google/uuid"
	"github.com/minio/minio-go/v7"
)

const (
	defaultPartSize = 32 << 20
)

func UploadHandler(minioSvc *service.MinIOService, cfg *config.Config, producer *service.KafkaProducer, kafkaTopic string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		accessToken, err := getCookieHandler(w, r)
		if err != nil {
			RespondError(w, http.StatusUnauthorized, "Не авторизованный пользователь!")
			return
		}

		authResp, statusCode := service.IsAuthenticated(accessToken)
		if statusCode != http.StatusOK {
			RespondError(w, statusCode, authResp.Error)
			return
		}

		filePart, err := getFilePart(w, r)
		if err != nil {
			return
		}
		defer filePart.Close()

		fullReader, isVideo, err := service.IsVideoFile(filePart, filePart.FileName())
		if err != nil {
			RespondError(w, http.StatusBadRequest, fmt.Sprintf("Ошибка проверки файла: %v", err))
			return
		}
		if !isVideo {
			RespondError(w, http.StatusBadRequest, "Файл не является видео")
			return
		}

		videoID, fileName, err := uploadToMinIO(minioSvc, cfg, fullReader, filePart)
		if err != nil {
			log.Printf("Error upload: %v", err)
			RespondError(w, http.StatusInternalServerError, fmt.Sprintf("Ошибка загрузки: %v", err))
			return
		}

		if err := sendToKafka(producer, kafkaTopic, &authResp, minioSvc.UnprocessedVideosFolder, fileName, videoID); err != nil {
			log.Printf("Error send message: %v", err)
			RespondError(w, http.StatusInternalServerError, fmt.Sprintf("Ошибка отправки сообщения: %v", err))
			return
		}

		log.Printf("Message sent to Kafka: topic=%s key=%s value=%s\n", kafkaTopic, videoID.String(),
			fmt.Sprintf(`{"user_id": "%s", "video_path": "%s/%s"}`, authResp.User.ID, minioSvc.UnprocessedVideosFolder, fileName))

		JSONResponse(w, http.StatusOK, "Файл успешно создан")
	}
}

func getFilePart(w http.ResponseWriter, r *http.Request) (*multipart.Part, error) {
	reader, err := r.MultipartReader()
	if err != nil {
		RespondError(w, http.StatusBadRequest, fmt.Sprintf("Ошибка чтения файла: %v", err))
		return nil, err
	}

	for {
		part, err := reader.NextPart()
		if err == io.EOF {
			RespondError(w, http.StatusBadRequest, "Нет файла")
			return nil, err
		}
		if err != nil {
			RespondError(w, http.StatusBadRequest, fmt.Sprintf("Ошибка чтения части: %v", err))
			return nil, err
		}

		if part.FormName() == "file" {
			return part, nil
		}
	}
}

func uploadToMinIO(minioSvc *service.MinIOService, cfg *config.Config, reader io.Reader, part *multipart.Part) (uuid.UUID, string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	videoID, err := uuid.NewRandom()
	if err != nil {
		return uuid.Nil, "", fmt.Errorf("ошибка генерации uuid: %v", err)
	}

	ext := filepath.Ext(part.FileName())
	fileName := hex.EncodeToString(videoID[:]) + ext
	fullPath := minioSvc.UnprocessedVideosFolder + "/" + fileName

	_, err = minioSvc.Client.PutObject(ctx, cfg.Bucket, fullPath, reader, -1, minio.PutObjectOptions{
		ContentType: "application/octet-stream",
		PartSize:    defaultPartSize,
	})

	return videoID, fileName, err
}

func sendToKafka(producer *service.KafkaProducer, topic string, authResp *service.AuthResponse, folderPath, fileName string, videoID uuid.UUID) error {
	msg := map[string]any{
		"user_id":    authResp.User.ID,
		"video_path": folderPath + "/" + fileName,
	}

	msgBytes, err := json.Marshal(msg)
	if err != nil {
		return fmt.Errorf("ошибка формирования сообщения: %v", err)
	}

	return producer.SendMessage(topic, videoID.String(), msgBytes)
}
