package handler

import (
	"context"
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

func UploadHandler(minioSvc *service.MinIOService, cfg *config.Config, rabbitSvc *service.RabbitMQService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		accessToken, err := getCookieHandler(r, "access_token")
		if err != nil {
			RespondError(w, http.StatusUnauthorized, "Не авторизованный пользователь!")
			return
		}

		authResp, statusCode := service.IsAuthenticated(accessToken)
		if statusCode != http.StatusOK {
			RespondError(w, statusCode, authResp.Msg)
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

		videoPath := fmt.Sprintf("%s/%s", minioSvc.UnprocessedVideosFolder, fileName)
		if err := rabbitSvc.PublishVideoUploadEvent(videoPath, authResp.User.ID); err != nil {
			log.Printf("Error send message: %v", err)
			RespondError(w, http.StatusInternalServerError, fmt.Sprintf("Ошибка отправки сообщения: %v", err))
			return
		}

		log.Printf("Message sent to RabbitMQ: queue=unprocessed_video_uploaded video_id=%s user_id=%d video_path=%s\n",
			videoID.String(), authResp.User.ID, videoPath)

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
	ctx, cancel := context.WithTimeout(context.Background(), cfg.MinioTimeout*time.Second)
	defer cancel()

	videoID, err := uuid.NewRandom()
	if err != nil {
		return uuid.Nil, "", fmt.Errorf("ошибка генерации uuid: %v", err)
	}

	ext := filepath.Ext(part.FileName())
	fileName := videoID.String() + ext
	fullPath := minioSvc.UnprocessedVideosFolder + "/" + fileName

	_, err = minioSvc.Client.PutObject(ctx, cfg.Bucket, fullPath, reader, -1, minio.PutObjectOptions{
		ContentType: "application/octet-stream",
		PartSize:    defaultPartSize,
	})

	return videoID, fileName, err
}
