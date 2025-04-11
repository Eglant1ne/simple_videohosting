package handler

import (
	"io"
	"net/http"

	"github.com/Eglant1ne/simple_videohosting/services/file_upload_service/internal/service"
	"github.com/google/uuid"
)

func uploadFileInChunks(s3svc *service.S3Service) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		chunk, err := io.ReadAll(r.Body)
		if err != nil {
			http.Error(w, "failed to read body", http.StatusBadRequest)
			return
		}

		key := "chunk_" + uuid.New().String()
		if err := s3svc.UploadChunk(r.Context(), key, chunk); err != nil {
			http.Error(w, "chunk upload error", http.StatusInternalServerError)
			return
		}

		w.Write([]byte("chunk uploaded: " + key))
	}
}
