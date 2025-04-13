package handler

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"sync"
	"time"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/config"
	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	"github.com/minio/minio-go/v7"
)

const (
	tmpDir    = "../.././tmp"
	chunksDir = "../.././tmp/chunks"

	chunkPattern  = "chunk_%03d.mp4"
	chunkDuration = 5
	maxUploadSize = 20 << 30
)

type UploadResponse struct {
	Message        string `json:"message"`
	FinalObjectKey string `json:"final_object_key,omitempty"`
}

func UploadHandler(minioClient *service.MinIOService, cfg *config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		r.Body = http.MaxBytesReader(w, r.Body, maxUploadSize)

		if r.Method != http.MethodPost {
			http.Error(w, "Метод не поддерживается", http.StatusMethodNotAllowed)
			return
		}

		err := r.ParseMultipartForm(10 << 20)
		if err != nil {
			http.Error(w, "Ошибка парсинга формы: "+err.Error(), http.StatusBadRequest)
			return
		}

		file, fileHeader, err := r.FormFile("file")
		if err != nil {
			http.Error(w, "Ошибка получения файла: "+err.Error(), http.StatusBadRequest)
			return
		}
		defer file.Close()

		tmpFilePath := filepath.Join(tmpDir, fileHeader.Filename)
		outFile, err := os.Create(tmpFilePath)
		if err != nil {
			http.Error(w, "Ошибка создания временного файла: "+err.Error(), http.StatusInternalServerError)
			return
		}
		defer outFile.Close()

		if _, err = io.Copy(outFile, file); err != nil {
			http.Error(w, "Ошибка сохранения файла: "+err.Error(), http.StatusInternalServerError)
			return
		}
		log.Printf("Файл %s успешно сохранён", tmpFilePath)

		// Разбиваем видео на чанки
		if err = splitVideo(tmpFilePath, chunksDir); err != nil {
			http.Error(w, "Ошибка разбиения видео: "+err.Error(), http.StatusInternalServerError)
			return
		}

		chunkFiles, err := filepath.Glob(filepath.Join(chunksDir, "chunk_*.mp4"))
		if err != nil || len(chunkFiles) == 0 {
			http.Error(w, "Чанки не найдены", http.StatusInternalServerError)
			return
		}
		sort.Strings(chunkFiles)

		finalObjectKey := fmt.Sprintf("%s_final_%d.mp4", fileHeader.Filename, time.Now().Unix())
		ctx := context.Background()

		coreClient := &minio.Core{Client: minioClient.Client}

		if err = uploadVideoInChunks(ctx, coreClient, cfg.Bucket, finalObjectKey, chunkFiles); err != nil {
			http.Error(w, "Ошибка загрузки файла: "+err.Error(), http.StatusInternalServerError)
			return
		}

		resp := UploadResponse{
			Message:        "Видео успешно загружено и обработано",
			FinalObjectKey: finalObjectKey,
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}
}

func splitVideo(inputFile, outputDir string) error {
	errCh := make(chan error)

	go func() {
		outputPattern := filepath.Join(outputDir, chunkPattern)
		cmd := exec.Command("ffmpeg",
			"-i", inputFile,
			"-c", "copy",
			"-map", "0",
			"-segment_time", strconv.Itoa(chunkDuration),
			"-f", "segment",
			outputPattern,
		)

		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr

		errCh <- cmd.Run()
	}()

	return <-errCh
}

func uploadVideoInChunks(ctx context.Context, core *minio.Core, bucketName, objectName string, chunkFiles []string) error {
	uploadID, err := core.NewMultipartUpload(ctx, bucketName, objectName, minio.PutObjectOptions{})
	if err != nil {
		return fmt.Errorf("ошибка инициализации multipart upload: %v", err)
	}
	log.Printf("Начат multipart upload. UploadID: %s", uploadID)

	var wg sync.WaitGroup
	partCh := make(chan minio.CompletePart, len(chunkFiles))
	errCh := make(chan error, len(chunkFiles))

	for idx, chunkPath := range chunkFiles {
		wg.Add(1)
		go func(partNumber int, chunkPath string) {
			defer wg.Done()

			file, err := os.Open(chunkPath)
			if err != nil {
				errCh <- fmt.Errorf("ошибка открытия файла %s: %v", chunkPath, err)
				return
			}
			defer file.Close()

			stat, err := file.Stat()
			if err != nil {
				errCh <- fmt.Errorf("ошибка получения размера файла %s: %v", chunkPath, err)
				return
			}

			partInfo, err := core.PutObjectPart(ctx, bucketName, objectName, uploadID, partNumber, file, stat.Size(), minio.PutObjectPartOptions{})
			if err != nil {
				errCh <- fmt.Errorf("ошибка загрузки части %d: %v", partNumber, err)
				return
			}

			log.Printf("Загружена часть %d, ETag: %s", partNumber, partInfo.ETag)

			partCh <- minio.CompletePart{
				ETag:       partInfo.ETag,
				PartNumber: partNumber,
			}
		}(idx+1, chunkPath)
	}

	go func() {
		wg.Wait()
		close(partCh)
		close(errCh)
	}()

	var completeParts []minio.CompletePart

	for part := range partCh {
		completeParts = append(completeParts, part)
	}

	if len(errCh) > 0 {
		_ = core.AbortMultipartUpload(ctx, bucketName, objectName, uploadID)
		for e := range errCh {
			log.Println(e)
		}
		return fmt.Errorf("одна или несколько частей не были загружены")
	}

	_, err = core.CompleteMultipartUpload(ctx, bucketName, objectName, uploadID, completeParts, minio.PutObjectOptions{})
	if err != nil {
		_ = core.AbortMultipartUpload(ctx, bucketName, objectName, uploadID)
		return fmt.Errorf("ошибка завершения multipart upload: %v", err)
	}

	log.Printf("Multipart upload завершён для %s", objectName)
	return nil
}
