package handler

import (
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
	chunksDir     = "../.././tmp/chunks"
	chunkPattern  = "chunk_%03d.mp4"
	chunkDuration = 5
	maxUploadSize = 20 << 30
	minPartSize   = 5 * 1024 * 1024 // Минимальный размер чанка (5MB)
)

type UploadResponse struct {
	Message        string `json:"message"`
	FinalObjectKey string `json:"final_object_key,omitempty"`
}

func UploadHandler(minioSvc *service.MinIOService, cfg *config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		r.Body = http.MaxBytesReader(w, r.Body, maxUploadSize)

		if err := r.ParseMultipartForm(10 << 20); err != nil {
			http.Error(w, "Ошибка парсинга формы: "+err.Error(), http.StatusBadRequest)
			return
		}

		file, fileHeader, err := r.FormFile("file")
		if err != nil {
			http.Error(w, "Ошибка получения файла: "+err.Error(), http.StatusBadRequest)
			return
		}
		defer file.Close()

		finalObjectKey := fmt.Sprintf("%s_final_%d.mp4", fileHeader.Filename, time.Now().Unix())
		coreClient := &minio.Core{Client: minioSvc.Client}

		uploadID, err := coreClient.NewMultipartUpload(ctx, cfg.Bucket, finalObjectKey, minio.PutObjectOptions{})
		if err != nil {
			http.Error(w, "Ошибка инициализации multipart upload: "+err.Error(), http.StatusInternalServerError)
			return
		}

		log.Printf("Multipart upload initiated: UploadID=%s", uploadID)

		if err := os.MkdirAll(chunksDir, 0755); err != nil {
			http.Error(w, "Ошибка создания папки чанков: "+err.Error(), http.StatusInternalServerError)
			return
		}

		_ = cleanChunksDir(chunksDir)

		pr, pw := io.Pipe()

		go func() {
			defer pw.Close()
			io.Copy(pw, file)
		}()

		// ffmpeg setup
		cmd := exec.Command("ffmpeg",
			"-i", "pipe:0",
			"-c", "copy",
			"-map", "0",
			"-f", "segment",
			"-segment_time", strconv.Itoa(chunkDuration),
			filepath.Join(chunksDir, chunkPattern),
		)
		cmd.Stdin = pr
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr

		if err := cmd.Start(); err != nil {
			http.Error(w, "Ошибка запуска ffmpeg: "+err.Error(), http.StatusInternalServerError)
			return
		}

		var (
			wg            sync.WaitGroup
			partNumber    = 1
			completeParts []minio.CompletePart
			uploadErr     error
			mu            sync.Mutex
		)

		done := make(chan struct{})
		go func() {
			defer close(done)

			for {
				files, err := filepath.Glob(filepath.Join(chunksDir, "chunk_*.mp4"))
				if err != nil {
					log.Println("Ошибка при поиске чанков:", err)
					break
				}
				sort.Strings(files)

				for len(files) > 0 {
					chunk := files[0]
					files = files[1:]

					wg.Add(1)
					go func(partNum int, chunkPath string) {
						defer wg.Done()

						f, err := os.Open(chunkPath)
						if err != nil {
							log.Printf("Ошибка открытия чанка: %v", err)
							return
						}
						defer f.Close()

						stat, err := f.Stat()
						if err != nil {
							log.Printf("Ошибка чтения размера чанка: %v", err)
							return
						}

						if stat.Size() < minPartSize && len(files) > 0 {
							log.Printf("Пропущен чанк %d: меньше 5MB", partNum)
							return
						}

						partInfo, err := coreClient.PutObjectPart(ctx, cfg.Bucket, finalObjectKey, uploadID, partNum, f, stat.Size(), minio.PutObjectPartOptions{})
						if err != nil {
							log.Printf("Ошибка загрузки чанка %d: %v", partNum, err)
							uploadErr = err
							return
						}

						log.Printf("Чанк %d загружен, ETag: %s", partNum, partInfo.ETag)

						mu.Lock()
						completeParts = append(completeParts, minio.CompletePart{
							ETag:       partInfo.ETag,
							PartNumber: partNum,
						})
						mu.Unlock()

						_ = os.Remove(chunkPath)
					}(partNumber, chunk)

					partNumber++
				}

				if cmd.ProcessState != nil && cmd.ProcessState.Exited() {
					break
				}
				time.Sleep(500 * time.Millisecond)
			}
		}()

		if err := cmd.Wait(); err != nil {
			http.Error(w, "Ошибка обработки видео: "+err.Error(), http.StatusInternalServerError)
			return
		}

		<-done
		wg.Wait()

		if uploadErr != nil {
			_ = coreClient.AbortMultipartUpload(ctx, cfg.Bucket, finalObjectKey, uploadID)
			http.Error(w, "Ошибка при multipart upload", http.StatusInternalServerError)
			return
		}
		sort.Slice(completeParts, func(i, j int) bool {
			return completeParts[i].PartNumber < completeParts[j].PartNumber
		})

		_, err = coreClient.CompleteMultipartUpload(ctx, cfg.Bucket, finalObjectKey, uploadID, completeParts, minio.PutObjectOptions{})
		if err != nil {
			_ = coreClient.AbortMultipartUpload(ctx, cfg.Bucket, finalObjectKey, uploadID)
			http.Error(w, "Ошибка завершения multipart upload: "+err.Error(), http.StatusInternalServerError)
			return
		}

		log.Printf("Multipart upload завершён: %s", finalObjectKey)

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(UploadResponse{
			Message:        "Видео успешно загружено",
			FinalObjectKey: finalObjectKey,
		})
	}
}

func cleanChunksDir(dir string) error {
	files, err := filepath.Glob(filepath.Join(dir, "chunk_*.mp4"))
	if err != nil {
		return err
	}
	for _, f := range files {
		os.Remove(f)
	}
	return nil
}
